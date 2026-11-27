---
sidebar_position: 5
---

# Structs

```metel
struct Point {
    x: f64,
    y: f64,
}

fun main() -> i64 {
    let p := Point(x = 1.0, y = 2.0);
    return p.y as i64;
}
```

## Methods

```metel
struct Point {
    x: f64,
    y: f64,
}

extend Point {
    fun distance(self, other: Point) -> f64 {
        let dx := self.x - other.x;
        let dy := self.y - other.y;
        return dx * dx + dy * dy;   // squared distance
    }
}

fun main() -> i64 {
    let p := Point(x = 1.0, y = 2.0);
    let q := Point(x = 4.0, y = 6.0);
    let d := p.distance(q);
    return d as i64;
}
```

`self` refers to the receiver. Methods are called with dot syntax.

## Generic Structs

```metel
struct Pair<A, B> {
    first: A,
    second: B,
}

fun main() -> i64 {
    let p := Pair(first = 1, second = true);
    return p.first;
}
```

---
