package api

import (
    "database/sql"
    "encoding/json"
    "net/http"
    "strings"
    "time"

    "github.com/go-chi/chi/v5"
)

type SyncAPI struct{ DB *sql.DB }

func (s *SyncAPI) Routes() chi.Router {
    r := chi.NewRouter()
    r.Get("/pull", s.pull)
    r.Post("/push", s.push)
    return r
}

func (s *SyncAPI) pull(w http.ResponseWriter, r *http.Request) {
    uid := userID(r)
    since := r.URL.Query().Get("since")
    if since == "" { since = "1970-01-01T00:00:00Z" }

    query := func(table string) ([]map[string]any, error) {
        rows, err := s.DB.Query(`SELECT * FROM `+table+` WHERE user_id=? AND updated_at > ?`, uid, since)
        if err != nil { return nil, err }
        defer rows.Close()
        cols, _ := rows.Columns()
        var out []map[string]any
        for rows.Next() {
            vals := make([]any, len(cols))
            ptrs := make([]any, len(cols))
            for i := range vals { ptrs[i] = &vals[i] }
            if err := rows.Scan(ptrs...); err != nil { return nil, err }
            m := map[string]any{}
            for i, c := range cols { m[c] = vals[i] }
            out = append(out, m)
        }
        return out, nil
    }

    payload := map[string]any{}
    for _, t := range []string{"categories","sources","rules","operations"} {
        data, err := query(t); if err != nil { http.Error(w, err.Error(), 500); return }
        payload[t] = data
    }
    payload["server_time"] = time.Now().UTC().Format(time.RFC3339)
    json.NewEncoder(w).Encode(payload)
}

func (s *SyncAPI) push(w http.ResponseWriter, r *http.Request) {
    uid := userID(r)
    var body map[string][]map[string]any
    if err := json.NewDecoder(r.Body).Decode(&body); err != nil { http.Error(w, err.Error(), 400); return }

    tx, err := s.DB.Begin(); if err != nil { http.Error(w, err.Error(), 500); return }
    defer tx.Rollback()

    upsert := func(table string, rows []map[string]any, cols []string) error {
        if len(rows)==0 { return nil }
        for _, row := range rows {
            // LWW: просто апсертим, полагаясь на client-side updated_at, сервер не отклоняет
            place := "(" + strings.Repeat("?,", len(cols)-1) + "?)"
            args := make([]any, 0, len(cols))
            for _, c := range cols { args = append(args, row[c]) }
            // ON CONFLICT(id) DO UPDATE SET ...
            set := ""
            for i, c := range cols {
                if c=="id" { continue }
                if i>0 { set += ", " }
                set += c + "=excluded." + c
            }
            _, err := tx.Exec(`INSERT INTO `+table+`(`+strings.Join(cols,",")+`) VALUES`+place+`
                ON CONFLICT(id) DO UPDATE SET `+set, args...)
            if err != nil { return err }
        }
        return nil
    }

    typeCols := map[string][]string{
        "categories": {"id","user_id","name","kind","icon","color","active","limit_type","limit_value","created_at","updated_at","deleted_at"},
        "sources":    {"id","user_id","name","currency","expected_date","icon","color","created_at","updated_at","deleted_at"},
        "rules":      {"id","user_id","source_id","category_id","percent","cap_cents","created_at","updated_at","deleted_at"},
        "operations": {"id","user_id","type","source_id","category_id","wallet","amount_cents","currency","rate","date","note","created_at","updated_at","deleted_at"},
    }

    for table, cols := range typeCols {
        rows := body[table]
        // гарантируем user_id = токену
        for i := range rows { rows[i]["user_id"] = uid }
        if err := upsert(table, rows, cols); err != nil { http.Error(w, err.Error(), 500); return }
    }

    if err := tx.Commit(); err != nil { http.Error(w, err.Error(), 500); return }
    w.WriteHeader(204)
}