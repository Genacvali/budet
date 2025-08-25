package internal

type User struct {
    ID, Email, PasswordHash, CreatedAt, UpdatedAt string
}

type Category struct {
    ID, UserID, Name, Kind, Icon, Color, LimitType string
    Active                                         bool
    LimitValue                                     float64
    CreatedAt, UpdatedAt, DeletedAt                *string
}

type Source struct {
    ID, UserID, Name, Currency, ExpectedDate, Icon, Color string
    CreatedAt, UpdatedAt, DeletedAt                       *string
}

type Rule struct {
    ID, UserID, SourceID, CategoryID string
    Percent                          float64
    CapCents                         *int64
    CreatedAt, UpdatedAt, DeletedAt  *string
}

type Operation struct {
    ID, UserID, Type, SourceID, CategoryID, Wallet, Currency, Date, Note string
    AmountCents int64
    Rate        float64
    CreatedAt, UpdatedAt, DeletedAt *string
}