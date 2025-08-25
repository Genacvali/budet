package api

import (
    "database/sql"
    "encoding/json"
    "net/http"
    "strings"
    "time"

    "golang.org/x/crypto/bcrypt"

    "budget-pwa/backend/internal"
    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"

    "github.com/google/uuid"
)

type AuthAPI struct{ DB *sql.DB }

func (a *AuthAPI) Routes() chi.Router {
    r := chi.NewRouter()
    r.Use(middleware.AllowContentType("application/json"))
    r.Post("/register", a.register)
    r.Post("/login", a.login)
    r.Get("/me", a.me)
    return r
}

type creds struct{ Email, Password string }

func (a *AuthAPI) register(w http.ResponseWriter, r *http.Request) {
    var c creds
    if err := json.NewDecoder(r.Body).Decode(&c); err != nil { http.Error(w, err.Error(), 400); return }
    c.Email = strings.TrimSpace(strings.ToLower(c.Email))
    if c.Email == "" || len(c.Password) < 6 { http.Error(w, "bad credentials", 400); return }

    pw, _ := bcrypt.GenerateFromPassword([]byte(c.Password), bcrypt.DefaultCost)
    now := time.Now().UTC().Format(time.RFC3339)
    id := uuid.NewString()

    _, err := a.DB.Exec(`INSERT INTO users(id,email,password_hash,created_at,updated_at) VALUES(?,?,?,?,?)`,
        id, c.Email, string(pw), now, now)
    if err != nil { http.Error(w, err.Error(), 409); return }

    token, _ := internal.MakeToken(id, c.Email, 30*24*time.Hour)
    json.NewEncoder(w).Encode(map[string]any{"token": token})
}

func (a *AuthAPI) login(w http.ResponseWriter, r *http.Request) {
    var c creds
    if err := json.NewDecoder(r.Body).Decode(&c); err != nil { http.Error(w, err.Error(), 400); return }
    row := a.DB.QueryRow(`SELECT id,password_hash,email FROM users WHERE email = ?`, strings.ToLower(c.Email))
    var id, hash, email string
    if err := row.Scan(&id, &hash, &email); err != nil { http.Error(w, "invalid login", 401); return }
    if bcrypt.CompareHashAndPassword([]byte(hash), []byte(c.Password)) != nil { http.Error(w, "invalid login", 401); return }
    token, _ := internal.MakeToken(id, email, 30*24*time.Hour)
    json.NewEncoder(w).Encode(map[string]any{"token": token})
}

func (a *AuthAPI) me(w http.ResponseWriter, r *http.Request) {
    claims := r.Context().Value("claims").(*internal.Claims)
    json.NewEncoder(w).Encode(map[string]any{"user_id": claims.UserID, "email": claims.Email})
}