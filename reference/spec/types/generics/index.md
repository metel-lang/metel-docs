---
sidebar_position: 12
---

# Generics

Types and functions can be parameterized with `<T>` syntax.

```metel
struct Stack<T> {
    items: [T],
}

fun first<T>(arr: [T]) -> Option<T> {
    if (arr.len() == 0) {
        return None;
    }
    return Some { value = arr[0] };
}

fun main() -> i64 {
    let stack := Stack { items = [1, 2, 3] };
    match (first(stack.items)) {
        Some { value } => value,
        None => 0,
    }
}
```
