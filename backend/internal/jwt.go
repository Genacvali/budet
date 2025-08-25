package internal

import (
    "errors"
    "os"
    "github.com/golang-jwt/jwt/v5"
    "time"
)

func getJWTKey() []byte {
    if secret := os.Getenv("JWT_SECRET"); secret != "" {
        return []byte(secret)
    }
    return []byte("CHANGE_ME_SUPER_SECRET_DEFAULT_KEY")
}

type Claims struct {
    UserID string `json:"uid"`
    Email  string `json:"eml"`
    jwt.RegisteredClaims
}

func MakeToken(uid, email string, ttl time.Duration) (string, error) {
    claims := &Claims{
        UserID: uid, Email: email,
        RegisteredClaims: jwt.RegisteredClaims{
            ExpiresAt: jwt.NewNumericDate(time.Now().Add(ttl)),
            IssuedAt:  jwt.NewNumericDate(time.Now()),
        },
    }
    return jwt.NewWithClaims(jwt.SigningMethodHS256, claims).SignedString(getJWTKey())
}

func ParseToken(t string) (*Claims, error) {
    token, err := jwt.ParseWithClaims(t, &Claims{}, func(token *jwt.Token) (interface{}, error) { return getJWTKey(), nil })
    if err != nil { return nil, err }
    if claims, ok := token.Claims.(*Claims); ok && token.Valid {
        return claims, nil
    }
    return nil, errors.New("invalid token")
}