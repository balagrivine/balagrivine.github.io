---
title: "Everybody hates singletons!"
date: 2025-09-13 11:37:40 +0000
categories: [Golang]
tags: ["golang", "software design patterns"]
image:
  path: https://cdn.hashnode.com/res/hashnode/image/stock/unsplash/-S2-AKdWQoQ/upload/59b38c877968264df728792040706cd2.jpeg
---

If you’re from an OOP background or a design-patterns enthusiast like me, you’ve definitely come across the Singleton pattern. It was popularized by the Gang of Four in [*Design Patterns: Elements of Reusable Object-Oriented Software*](https://www.amazon.com/Design-Patterns-Elements-Reusable-Object-Oriented/dp/0201633612/?tag=offa01-20) over 30 years ago.

On paper, a singleton looks neat. It guarantees only one instance of a class and provides a global point of access. In Go, it’s tempting to reach for singletons when you want to prevent multiple goroutines from stomping on shared resources like initializing a database pool just once.

With a bit of *vibes and inshallah* engineering, you throw the database pool into a global variable so everything can reuse it. But this convenience quickly turns toxic; global mutable state, fragile life cycle management, and collisions between multiple callers.

```go
package pg

import(
	"context"
    "fmt"
	"log"
	"os"
	"sync"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	pgxdecimal "github.com/jackc/pgx-shopspring-decimal"
	pgxUUID "github.com/vgarvardt/pgx-google-uuid/v5"

	_ "github.com/lib/pq"
)

var (
	dbPool *pgxpool.Pool
	dbOnce     sync.Once
)

func NewDBPool(ctx context.Context) (*pgxpool.Pool, error) {
	dbURL := os.Getenv("DATABASE_URL")

	config, err := pgxpool.ParseConfig(dbURL)
	if err != nil {
		return nil, err
	}

	dbOnce.Do(func() {
		db, err := pgxpool.NewWithConfig(ctx, config)
		if err != nil {
			return nil, fmt.Errorf("failed to initialize database pool: %w", err)
		}

		db.Config().AfterConnect = func(ctx context.Context, conn *pgx.Conn) error {
			pgxdecimal.Register(conn.TypeMap())
			pgxUUID.Register(conn.TypeMap())

			return nil
		}

		dbPool = db
	})

	return dbPool, nil
}
```

For those who are unfamiliar with Go, `sync.Once` is a synchronization primitive designed to ensure that a specific block of code is executed only once, regardless of how many goroutines attempt to execute it concurrently. So in our example above, any goroutine calling `NewDBPool` after the dbPool variable has been initialized will always return the value in that variable instead of creating a new connection pool.

One thing that singleton pattern introduces in our program is global mutable state. However, the problem with global state is that it makes the program state unpredictable. Lets work with 2 scenarios expressed in the code below.

```go
package user

import (
"context"
"fmt"
"time"

"github.com/balagrivine/singleton/pg"
)

func Exists(ctx context.Context, userID string) (bool, error){
    query := `SELECT EXISTS(SELECT 1 FROM users WHERE user_id = $1)`
    timeout := 5 * time.Second
    ctx = context.WithTimeout(ctx, timeout)

    db, err := pg.NewDBPool(ctx)
    if err != nil{
        return fmt.Errorf("failed create database pool: %w", err)
    }
    defer db.Close()

    var exists bool
    err = db.QueryRow(ctx, query, userID).Scan(&exists)
    if err != nil{
        return false, fmt.Errorf("error checking if user exists: %w", err)
    }

    return true, nil
}
```

This code really looks nice, just that there is a terrible problem hiding in it. If 10 goroutines call `Exists`, the first one that defers `db.Close()` will shut down the pool for everyone else and the program will start failing in unpredictable ways.

The other downside of the singleton pattern is that it makes reasoning about tests really difficult. Suppose I want to test a function that calls the `Exists` method, how do I go about that without spinning up an actual database.

### The solution

Now that we have discussed some of the shortcomings of singletons, let’s unravel an alternative to singletons that when applied will yield much better results

### Dependency Injection

Dependency injection a software development technique that revolves around providing dependencies to an object from external sources rather than creating them within the object itself.

DI encourages explicit dependencies, while singletons encourage *hidden dependencies*. This is the real architectural advantage beyond just avoiding global state.

Let’s explore how we can use dependency injection to rework our previous solution and come up with cleaner code that is much simpler and easy to reason about.

```go
package pg

import(
	"context"
	"log"
	"os"
	"sync"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	pgxdecimal "github.com/jackc/pgx-shopspring-decimal"
	pgxUUID "github.com/vgarvardt/pgx-google-uuid/v5"

	_ "github.com/lib/pq"
)

type dbClient struct{
    db *pgxpool.Pool
}

func NewDBPool(ctx context.Context) (*DBClient, error) {
	dbURL := os.Getenv("DATABASE_URL")

	config, err := pgxpool.ParseConfig(dbURL)
	if err != nil {
		return nil, err
	}

	db, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize database pool: %w", err)
	}

	db.Config().AfterConnect = func(ctx context.Context, conn *pgx.Conn) error {
		pgxdecimal.Register(conn.TypeMap())
		pgxUUID.Register(conn.TypeMap())

		return nil
	}
    return &dbClient{
        db: db,
    }, nil
}

func (cl *dbClient)Exists(ctx context.Context, userID string) (bool, error){
    query := `SELECT EXISTS(SELECT 1 FROM users WHERE user_id = $1)`
    timeout := 5 * time.Second
    ctx = context.WithTimeout(ctx, timeout)

    var exists bool
    err := cl.db.QueryRow(ctx, query, userID).Scan(&exists)
    if err != nil{
        return false, fmt.Errorf("error checking if user exists: %w", err)
    }

    return exists, nil
}
```

```go
package user

import (
"context"
"fmt"
"time"

"github.com/balagrivine/singleton/pg"
)

type querier interface{
    Exists(ctx context.Context, userID string) (bool, error)
}

type userService struct{
    db querier
}

func NewService(db querier) *userService{
    return &UserService{
        db: db,
    }
}

func (usr *userService) SomeOperation(ctx context.Context, userID string) error{
    exists, err := usr.db.Exists(ctx, userID)
    if err != nil{
        return fmt.Errorf("SomeOperaton failed: %w", err)
    }

    if !exists{
        return errors.New("404 not found")
    }

    return nil
}
```

Now within the main package, we can initialize the database and explicitly pass it inside the userService as a dependency, that way we can always create mocks or run a real database with test-containers if we want to write unit tests for any component within the code.

```go
package main

import (
"context"
"fmt"
"time"
"log"

"github.com/balagrivine/singleton/pg"
"github.com/balagrivine/singleton/user"
)

func main(){
    ctx := context.Background()

    pgClient, err := pg.NewDBPool(ctx)
    if err != nil{
        log.Fatal(err)
    }

    userService := user.NewService(pgClient)
    userID := "123"

    //Now we can call any user related operation without risking catastrophic failures
    // related to global mutable state
    err := userService.SomeOperation(ctx, userID)
    if err != nil{
        log.Fatal(err)
    }
}
```

With dependency injection, we have passed the database pool dependency explicitly to the user service, so if we need to write any unit test for the userservice, we can create mock implementation that satisfy the `querier` interface, thanks to Golang interfaces that are satisfied implicitly.

### What about testing

Well now with DI, writing unit tests stops being a headache and actually becomes fun. In this case, we’re going to test `SomeOperation`. Remember, the whole point of a unit test is to make sure a single component of our application behaves correctly. And here, our only mission is to confirm that `SomeOperation` does its job perfectly — without dragging the database along.

```go
package user_test

import (
	"context"
	"errors"
	"testing"

	"github.com/balagrivine/singleton/user"
)

type mockDB struct {
	existsFunc func(ctx context.Context, userID string) (bool, error)
}

func (m *mockDB) Exists(ctx context.Context, userID string) (bool, error) {
	return m.existsFunc(ctx, userID)
}

func TestSomeOperation(t *testing.T) {
	tests := []struct {
		name      string
		mock      func() *mockDB
		userID    string
		wantErr   bool
		wantError error
	}{
		{
			name: "user exists",
			mock: func() *mockDB {
				return &mockDB{
					existsFunc: func(ctx context.Context, userID string) (bool, error) {
						return true, nil
					},
				}
			},
			userID:  "123",
			wantErr: false,
		},
		{
			name: "user does not exist",
			mock: func() *mockDB {
				return &mockDB{
					existsFunc: func(ctx context.Context, userID string) (bool, error) {
						return false, nil
					},
				}
			},
			userID:    "456",
			wantErr:   true,
			wantError: errors.New("404 not found"),
		},
		{
			name: "database error",
			mock: func() *mockDB {
				return &mockDB{
					existsFunc: func(ctx context.Context, userID string) (bool, error) {
						return false, errors.New("db connection failed")
					},
				}
			},
			userID:    "789",
			wantErr:   true,
			wantError: errors.New("SomeOperaton failed: db connection failed"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			us := user.NewService(tt.mock())
			err := us.SomeOperation(t.Context(), tt.userID)

			if (err != nil) != tt.wantErr {
				t.Fatalf("expected error: %v, got: %v", tt.wantErr, err)
			}

			if tt.wantErr && err.Error() != tt.wantError.Error() {
				t.Errorf("expected error %q, got %q", tt.wantError, err)
			}
		})
	}
}
```

Our `mockDB` type has the Exists method, meaning it satisfies the querier interface, we can safely pass in mockDB as an argument to any function that accepts the querier interface.

With that said, there are areas where singletons still serve as the most reasonable approach to solve a particular problem. My mantra is always `use it only when you have to use it` and this is justified by the YAGNI principle.

My most common use case for singleton is in tests when I am using the TestMain function. This is where I have to initialize a database connection is tests using test-containers and I find the singleton pattern very useful. This is because in tests, the *scope is already global and short-lived*, so the downsides don’t matter as much.

If you find yourself reaching for singletons too often, step back. It’s usually a sign of hidden dependencies that should be made explicit.

### Conclusion

Use singletons sparingly, when the trade-offs are acceptable (e.g., short-lived test scope). Otherwise, DI gives you flexibility, testability, and clearer code.

Remember: [**Clear is better than clever**](https://www.youtube.com/watch?v=PAAkCSZUG1c&t=14m35s).

See you in my next blog…
