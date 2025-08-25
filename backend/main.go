package main

import (
    "context"
    "database/sql"
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
            http.Error(w, "no auth", http.StatusUnauthorized)
            return
        }
        token := strings.TrimPrefix(auth, "Bearer ")
        claims, err := internal.ParseToken(token)
        if err != nil {
            http.Error(w, "bad token", http.StatusUnauthorized)
            return
        }
        ctx := context.WithValue(r.Context(), "claims", claims)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

func mustApplyMigrations(db *sql.DB) {
    schemaPath := "db/migrate.sql"
    if _, err := os.Stat(schemaPath); err != nil {
        // поддержка альтернативного пути, если запускаем из корня репо
        schemaPath = "backend/db/migrate.sql"
    }
    b, err := os.ReadFile(schemaPath)
    if err != nil {
        log.Fatalf("read migrate.sql: %v", err)
    }
    if _, err := db.Exec(string(b)); err != nil {
        log.Fatalf("apply migrate.sql: %v", err)
    }
}

func main() {
    dbPath := "./data/budget.db"
    if env := os.Getenv("DB_PATH"); env != "" {
        dbPath = env
    }
    sqlDB, err := db.Open(dbPath)
    if err != nil {
        log.Fatal(err)
    }
    mustApplyMigrations(sqlDB)

    r := chi.NewRouter()
    r.Use(cors.Handler(cors.Options{
        AllowedOrigins:   []string{"*"}, // если фронт на том же домене — оставь *, иначе укажи точный origin
        AllowedMethods:   []string{"GET", "POST", "OPTIONS"},
        AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type"},
        AllowCredentials: true,
        MaxAge:           300,
    }))

    // Публичные маршруты
    auth := &api.AuthAPI{DB: sqlDB}
    r.Mount("/api/auth", auth.Routes())

    // Закрытые маршруты
    protected := chi.NewRouter()
    protected.Use(authMiddleware)

    entities := &api.EntitiesAPI{DB: sqlDB}
    sync := &api.SyncAPI{DB: sqlDB}

    protected.Mount("/api/entities", entities.Routes())
    protected.Mount("/api/sync", sync.Routes())

    // Вешаем защищённые подроуты на основной роутер
    r.Mount("/", protected)

    srv := &http.Server{
        Addr:              ":8080",
        Handler:           r,
        ReadHeaderTimeout: 5 * time.Second,
    }
    log.Println("API on :8080")
    log.Fatal(srv.ListenAndServe())
}