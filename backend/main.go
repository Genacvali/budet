package main

import (
    "context"
    "io"
    "log"
    "net/http"
    "os"
    "strings"
    "time"

    "budget-pwa/backend/api"
    "budget-pwa/backend/db"
    "budget-pwa/backend/internal"

    "github.com/go-chi/chi/v5"
    "github.com/go-chi/cors"
)

func authMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        auth := r.Header.Get("Authorization")
        if !strings.HasPrefix(auth, "Bearer ") {
            http.Error(w, "no auth", 401); return
        }
        token := strings.TrimPrefix(auth, "Bearer ")
        claims, err := internal.ParseToken(token)
        if err != nil { http.Error(w, "bad token", 401); return }
        ctx := context.WithValue(r.Context(), "claims", claims)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

func main() {
    dbPath := "./data/budget.db"
    if env := os.Getenv("DB_PATH"); env != "" { dbPath = env }
    sqlDB, err := db.Open(dbPath); if err != nil { log.Fatal(err) }
    
    // Run migrations
    migrationFile, err := os.Open("db/migrate.sql")
    if err != nil { log.Fatal("Failed to open migration file:", err) }
    defer migrationFile.Close()
    
    migrationSQL, err := io.ReadAll(migrationFile)
    if err != nil { log.Fatal("Failed to read migration file:", err) }
    if _, err := sqlDB.Exec(string(migrationSQL)); err != nil { log.Fatal("Migration failed:", err) }

    r := chi.NewRouter()
    r.Use(cors.Handler(cors.Options{
        AllowedOrigins:   []string{"*"},
        AllowedMethods:   []string{"GET","POST","OPTIONS"},
        AllowedHeaders:   []string{"Accept","Authorization","Content-Type"},
        AllowCredentials: true, MaxAge: 300,
    }))

    auth := &api.AuthAPI{DB: sqlDB}
    r.Route("/api/auth", func(rt chi.Router) { rt.Mount("/", auth.Routes()) })

    protected := chi.NewRouter()
    protected.Use(authMiddleware)
    
    entities := &api.EntitiesAPI{DB: sqlDB}
    sync := &api.SyncAPI{DB: sqlDB}
    protected.Mount("/api/entities", entities.Routes())
    protected.Mount("/api/sync", sync.Routes())
    
    r.Mount("/", protected)

    srv := &http.Server{
        Addr: ":8080", Handler: r, ReadHeaderTimeout: 5*time.Second,
    }
    log.Println("API on :8080")
    log.Fatal(srv.ListenAndServe())
}