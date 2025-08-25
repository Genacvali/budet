package api

import (
    "database/sql"
    "encoding/json"
    "net/http"
    "time"

    "budget-pwa/backend/internal"
    "github.com/go-chi/chi/v5"
    "github.com/google/uuid"
)

type EntitiesAPI struct{ DB *sql.DB }

func (e *EntitiesAPI) Routes() chi.Router {
    r := chi.NewRouter()
    r.Route("/categories", func(r chi.Router) {
        r.Get("/", e.listCategories)
        r.Post("/", e.upsertCategory)
    })
    r.Route("/sources", func(r chi.Router) {
        r.Get("/", e.listSources)
        r.Post("/", e.upsertSource)
    })
    r.Route("/operations", func(r chi.Router) {
        r.Get("/", e.listOperations)
        r.Post("/", e.upsertOperation)
    })
    return r
}

func userID(r *http.Request) string {
    return r.Context().Value("claims").(*internal.Claims).UserID
}

func (e *EntitiesAPI) listCategories(w http.ResponseWriter, r *http.Request) {
    uid := userID(r)
    rows, err := e.DB.Query(`SELECT id,user_id,name,kind,icon,color,active,limit_type,limit_value,created_at,updated_at,deleted_at
        FROM categories WHERE user_id = ? AND (deleted_at IS NULL)`, uid)
    if err != nil { http.Error(w, err.Error(), 500); return }
    defer rows.Close()
    var out []map[string]any
    for rows.Next() {
        var id, userID, name, kind, icon, color, limitType, createdAt, updatedAt string
        var active bool
        var limitValue float64
        var deletedAt *string
        if err := rows.Scan(&id,&userID,&name,&kind,&icon,&color,&active,&limitType,&limitValue,&createdAt,&updatedAt,&deletedAt); err!=nil{ http.Error(w, err.Error(), 500); return }
        out = append(out, map[string]any{
            "id":id,"user_id":userID,"name":name,"kind":kind,"icon":icon,"color":color,"active":active,"limit_type":limitType,"limit_value":limitValue,"created_at":createdAt,"updated_at":updatedAt,"deleted_at":deletedAt,
        })
    }
    json.NewEncoder(w).Encode(out)
}

func (e *EntitiesAPI) upsertCategory(w http.ResponseWriter, r *http.Request) {
    var body map[string]any
    if err := json.NewDecoder(r.Body).Decode(&body); err != nil { http.Error(w, err.Error(), 400); return }
    now := time.Now().UTC().Format(time.RFC3339)
    id, _ := body["id"].(string)
    if id == "" { id = uuid.NewString() }
    uid := userID(r)
    _, err := e.DB.Exec(`
INSERT INTO categories(id,user_id,name,kind,icon,color,active,limit_type,limit_value,created_at,updated_at,deleted_at)
VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
ON CONFLICT(id) DO UPDATE SET
  name=excluded.name, kind=excluded.kind, icon=excluded.icon, color=excluded.color, active=excluded.active,
  limit_type=excluded.limit_type, limit_value=excluded.limit_value, updated_at=excluded.updated_at, deleted_at=excluded.deleted_at
`, id, uid, body["name"], body["kind"], body["icon"], body["color"], body["active"], body["limit_type"], body["limit_value"], now, now, body["deleted_at"])
    if err != nil { http.Error(w, err.Error(), 500); return }
    json.NewEncoder(w).Encode(map[string]string{"id": id, "updated_at": now})
}

func (e *EntitiesAPI) listSources(w http.ResponseWriter, r *http.Request) {
    uid := userID(r)
    rows, err := e.DB.Query(`SELECT id,user_id,name,currency,expected_date,icon,color,created_at,updated_at,deleted_at
        FROM sources WHERE user_id = ? AND (deleted_at IS NULL)`, uid)
    if err != nil { http.Error(w, err.Error(), 500); return }
    defer rows.Close()
    var out []map[string]any
    for rows.Next() {
        var id, userID, name, currency, createdAt, updatedAt string
        var expectedDate, icon, color, deletedAt *string
        if err := rows.Scan(&id,&userID,&name,&currency,&expectedDate,&icon,&color,&createdAt,&updatedAt,&deletedAt); err!=nil{ http.Error(w, err.Error(), 500); return }
        out = append(out, map[string]any{
            "id":id,"user_id":userID,"name":name,"currency":currency,"expected_date":expectedDate,"icon":icon,"color":color,"created_at":createdAt,"updated_at":updatedAt,"deleted_at":deletedAt,
        })
    }
    json.NewEncoder(w).Encode(out)
}

func (e *EntitiesAPI) upsertSource(w http.ResponseWriter, r *http.Request) {
    var body map[string]any
    if err := json.NewDecoder(r.Body).Decode(&body); err != nil { http.Error(w, err.Error(), 400); return }
    now := time.Now().UTC().Format(time.RFC3339)
    id, _ := body["id"].(string)
    if id == "" { id = uuid.NewString() }
    uid := userID(r)
    _, err := e.DB.Exec(`
INSERT INTO sources(id,user_id,name,currency,expected_date,icon,color,created_at,updated_at,deleted_at)
VALUES(?,?,?,?,?,?,?,?,?,?)
ON CONFLICT(id) DO UPDATE SET
  name=excluded.name, currency=excluded.currency, expected_date=excluded.expected_date, 
  icon=excluded.icon, color=excluded.color, updated_at=excluded.updated_at, deleted_at=excluded.deleted_at
`, id, uid, body["name"], body["currency"], body["expected_date"], body["icon"], body["color"], now, now, body["deleted_at"])
    if err != nil { http.Error(w, err.Error(), 500); return }
    json.NewEncoder(w).Encode(map[string]string{"id": id, "updated_at": now})
}

func (e *EntitiesAPI) listOperations(w http.ResponseWriter, r *http.Request) {
    uid := userID(r)
    rows, err := e.DB.Query(`SELECT id,user_id,type,source_id,category_id,wallet,amount_cents,currency,rate,date,note,created_at,updated_at,deleted_at
        FROM operations WHERE user_id = ? AND (deleted_at IS NULL) ORDER BY date DESC LIMIT 100`, uid)
    if err != nil { http.Error(w, err.Error(), 500); return }
    defer rows.Close()
    var out []map[string]any
    for rows.Next() {
        var id, userID, opType, categoryID, currency, date, createdAt, updatedAt string
        var sourceID, wallet, note, deletedAt *string
        var amountCents int64
        var rate float64
        if err := rows.Scan(&id,&userID,&opType,&sourceID,&categoryID,&wallet,&amountCents,&currency,&rate,&date,&note,&createdAt,&updatedAt,&deletedAt); err!=nil{ http.Error(w, err.Error(), 500); return }
        out = append(out, map[string]any{
            "id":id,"user_id":userID,"type":opType,"source_id":sourceID,"category_id":categoryID,"wallet":wallet,"amount_cents":amountCents,"currency":currency,"rate":rate,"date":date,"note":note,"created_at":createdAt,"updated_at":updatedAt,"deleted_at":deletedAt,
        })
    }
    json.NewEncoder(w).Encode(out)
}

func (e *EntitiesAPI) upsertOperation(w http.ResponseWriter, r *http.Request) {
    var body map[string]any
    if err := json.NewDecoder(r.Body).Decode(&body); err != nil { http.Error(w, err.Error(), 400); return }
    now := time.Now().UTC().Format(time.RFC3339)
    id, _ := body["id"].(string)
    if id == "" { id = uuid.NewString() }
    uid := userID(r)
    _, err := e.DB.Exec(`
INSERT INTO operations(id,user_id,type,source_id,category_id,wallet,amount_cents,currency,rate,date,note,created_at,updated_at,deleted_at)
VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
ON CONFLICT(id) DO UPDATE SET
  type=excluded.type, source_id=excluded.source_id, category_id=excluded.category_id, wallet=excluded.wallet,
  amount_cents=excluded.amount_cents, currency=excluded.currency, rate=excluded.rate, date=excluded.date,
  note=excluded.note, updated_at=excluded.updated_at, deleted_at=excluded.deleted_at
`, id, uid, body["type"], body["source_id"], body["category_id"], body["wallet"], body["amount_cents"], body["currency"], body["rate"], body["date"], body["note"], now, now, body["deleted_at"])
    if err != nil { http.Error(w, err.Error(), 500); return }
    json.NewEncoder(w).Encode(map[string]string{"id": id, "updated_at": now})
}