package api

import (
	"net/http"

	"github.com/labstack/echo/v4"
)

type Item struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

type store struct {
	items  []Item
	nextID int
}

func newStore() *store { return &store{items: []Item{}, nextID: 1} }

func NewEcho() *echo.Echo {
	e := echo.New()
	s := newStore()
	e.GET("/health", func(c echo.Context) error {
		return c.JSON(http.StatusOK, map[string]string{"status": "ok"})
	})
	e.GET("/items", func(c echo.Context) error {
		return c.JSON(http.StatusOK, s.items)
	})
	e.POST("/items", func(c echo.Context) error {
		var body struct {
			Name string `json:"name"`
		}
		if err := c.Bind(&body); err != nil {
			return c.JSON(http.StatusBadRequest, map[string]string{"error": "invalid JSON body"})
		}
		if body.Name == "" {
			return c.JSON(http.StatusBadRequest, map[string]string{"error": "name is required"})
		}
		item := Item{ID: s.nextID, Name: body.Name}
		s.nextID++
		s.items = append(s.items, item)
		return c.JSON(http.StatusCreated, item)
	})
	return e
}

func Handler() http.Handler { return NewEcho() }