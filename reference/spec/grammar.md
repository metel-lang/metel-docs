# Grammar

```
Program            → HeaderDecl* Declaration* EOF

HeaderDecl         → ImportDecl | ExportDecl

ImportDecl         → "import" ImportPath ";"
ExportDecl         → "export" ImportPath ";"
ImportPath         → PathRoot "." ImportTree
PathRoot           → "root" | "std" | "self" | "super" | IDENTIFIER
ImportTree         → ImportItem
                    | IDENTIFIER "." ImportTree
                    | "{" ImportItem ( "," ImportItem )* ","? "}"
                    | "*"
ImportItem         → IDENTIFIER ( "as" IDENTIFIER )?

> **Not yet implemented** — see `internal/rfcs/3-integrated/rfc-0099-dot-separated-module-paths.md` (issue #275). Path separator changed from `::` to `.`. Disambiguation is resolved at name-resolution time, not grammar time.

Declaration        → LetDeclaration
                    | VarDeclaration
                    | FunDeclaration
                    | StructDeclaration
                    | EnumDeclaration
                    | ExtendBlock
                    | AspectDeclaration
                    | Statement

LetDeclaration     → "let" IDENTIFIER ( ":" Type )? "=" Expression ";"
VarDeclaration     → "var" IDENTIFIER ( ":" Type )? "=" Expression ";"
FunDeclaration     → NativeBinding? "public"? "fun" IDENTIFIER GenericParams? "(" Params? ")" ( "->" Type )? WhereClause? ( Block | ";" )
NativeBinding      → "native" "(" "@" IDENTIFIER ( "." IDENTIFIER )* ")"  // standard library only
StructDeclaration  → "public"? "struct" IDENTIFIER GenericParams? ( ":" ExtendAspectList )? WhereClause? "{" StructFields "}"
EnumDeclaration    → "public"? "enum" IDENTIFIER GenericParams? ( ":" ExtendAspectList )? WhereClause? "{" EnumVariants "}"
ExtendBlock        → "extend" GenericParams? TypeExpr ( ":" ExtendAspectList )? WhereClause? ( "{" ( FunDeclaration | AssocTypeDef )* "}" | ";" )
AspectDeclaration  → "public"? "aspect" IDENTIFIER GenericParams? ( "{" ( AssocTypeDecl | AspectMethod )* "}" | ";" )
AspectMethod       → "fun" IDENTIFIER "(" Params? ")" ( "->" Type )? ( Block | ";" )
ExtendAspectList   → Bound ( "," Bound )*
AssocTypeDef       → "type" IDENTIFIER ( "=" Type )? ";"
AssocTypeDecl      → "type" IDENTIFIER ( ":" BoundList )? ";"

> **Not yet implemented** — see `internal/rfcs/3-integrated/rfc-0098-surface-keyword-renames.md` (issue #274). Keywords renamed: `impl` → `extend`, `pub` → `public`, `mut` → `var`.
> **Not yet implemented** — see `internal/rfcs/3-integrated/rfc-0102-bodyless-extend-blocks-for-marker-aspects-and-negative-impls.md` (issue #277). Bodyless `extend` blocks: `extend Type: Aspect;`.
> **Not yet implemented** — see `internal/rfcs/3-integrated/rfc-0103-marker-aspects-and-struct-embedded-aspect-lists.md` (issue #278). Bodyless aspect declarations: `aspect Name;`. Struct/enum embedded aspect lists: `struct Name: Aspects { ... }`.

Params             → Param ( "," Param )* ","?
Param              → ( "var" )? "self" | IDENTIFIER ( ":" Type )?
StructFields       → StructField ( "," StructField )* ","?
StructField        → "public"? IDENTIFIER ":" Type
EnumVariants       → EnumVariant ( "," EnumVariant )* ","?
EnumVariant        → IDENTIFIER ( "{" StructFields "}" )?
GenericParams      → "<" GenericParam ( "," GenericParam )* ">"
GenericParam       → IDENTIFIER ( ":" BoundList )?                      // since v0.7.0; RFC-0034
BoundList          → Bound ( "+" Bound )*                               // since v0.7.0; RFC-0034
Bound              → ( "!" )? BoundHead
BoundHead          → IDENTIFIER ( "<" TypeArgs ">" )? | "(" TypeList? ")" "->" Type
WhereClause        → "where" WhereConstraint ( "," WhereConstraint )*   // since v0.7.0; RFC-0002
WhereConstraint    → IDENTIFIER ":" BoundList                           // BoundList since v0.7.0; RFC-0034

Statement          → ExpressionStatement
                   | Block
                   | IfStatement
                   | WhileStatement
                   | ForStatement
                   | LoopStatement
                   | ReturnStatement
                   | BreakStatement
                   | ContinueStatement

ExpressionStatement → Expression ";"
Block               → "{" Declaration* "}"
IfStatement         → "if" "(" Expression ")" Block ( "else" ( IfStatement | Block ) )?
WhileStatement      → "while" "(" Expression ")" Block
ForStatement        → "for" "(" ForInit Expression? ";" Expression? ")" Block
                     | "for" "(" "let" IDENTIFIER "in" Expression ")" Block
                     | "for" "(" "var" IDENTIFIER "in" Expression ")" Block
ForInit             → VarDeclaration | ExpressionStatement | ";"
LoopStatement       → "loop" Block
ReturnStatement     → "return" Expression? ";"
BreakStatement      → "break" Expression? ";"
ContinueStatement   → "continue" ";"

Expression              → AssignmentExpression
AssignmentExpression    → LValue AssignOp AssignmentExpression | LogicalOrExpression
LValue                  → IDENTIFIER | CallExpression "." IDENTIFIER | CallExpression "[" Expression "]"
AssignOp                → "=" | "+=" | "-=" | "*=" | "/=" | "%="
LogicalOrExpression     → LogicalAndExpression ( "||" LogicalAndExpression )*
LogicalAndExpression    → ComparisonExpression ( "&&" ComparisonExpression )*
ComparisonExpression    → TermExpression ( ( ">" | ">=" | "<" | "<=" | "!=" | "==" ) TermExpression )?
TermExpression          → FactorExpression ( ( "+" | "-" ) FactorExpression )*
FactorExpression        → CastExpression ( ( "*" | "/" | "%" ) CastExpression )*
CastExpression          → AscribeExpression ( "as" Type )*
AscribeExpression       → UnaryExpression ( ":" Type )?
UnaryExpression         → ( "!" | "-" | "*" | "&" | "&var" ) UnaryExpression | PostfixExpression
PostfixExpression       → PrimaryExpression ( "(" Arguments? ")" | "." IDENTIFIER | ".<" TypeArgs ">" | "[" Expression "]" | "?" )*
Arguments               → CallArgument ( "," CallArgument )* ","?
CallArgument            → ( IDENTIFIER ":" Expression ) | Expression

> **Not yet implemented** — see `internal/rfcs/3-integrated/rfc-0100-constructor-call-construction.md` (issue #276). Keyword arguments in function calls: `fun(arg1: value1, arg2: value2)`. Struct literal syntax changed to `Type(field: value)`.

PrimaryExpression  → INT | FLOAT | STRING | "true" | "false" | "None" | "()"
                   | "(" Expression ( "," Expression )+ ")"   // tuple
                   | "(" Expression ")"
                   | "[" ( Expression ( "," Expression )* ","? )? "]"  // array literal
                   | "[" Expression ";" INT "]"                         // repeat construction [expr; N]
                   | Path
                   | StructLiteral
                   | MatchExpression
                   | IfExpression
                   | LoopExpression
                   | ClosureExpression

Path               → ( "root" | "std" | "self" | "super" | IDENTIFIER ) ( "." IDENTIFIER )*

> **Not yet implemented** — see `internal/rfcs/3-integrated/rfc-0099-dot-separated-module-paths.md` (issue #275). Path separator changed from `::` to `.`. Disambiguation is resolved at name-resolution time, not grammar time.

StructLiteral      → Path "(" CallArgument ( "," CallArgument )* ","? ")"

> **Not yet implemented** — see `internal/rfcs/3-integrated/rfc-0100-constructor-call-construction.md` (issue #276). Struct literal syntax changed from `Type { field: value }` to `Type(field: value)`. Pattern matching syntax unchanged.

MatchExpression    → "match" Expression "{" MatchArm ( "," MatchArm )* ","? "}"
MatchArm           → Pattern ( "if" Expression )? "=>" Expression
IfExpression       → "if" "(" Expression ")" Block "else" Block
LoopExpression     → "loop" Block
ClosureExpression  → "(" Params? ")" ( "->" Type )? Block

Pattern            → "_"
                    | "None"
                    | IDENTIFIER
                    | "(" Pattern ( "," Pattern )* ")"          // tuple pattern
                    | IDENTIFIER "." IDENTIFIER ( "{" PatternFields "}" )?
                    | INT | FLOAT | STRING | "true" | "false"
PatternFields      → IDENTIFIER ( "," IDENTIFIER )*

> **Not yet implemented** — see `internal/rfcs/3-integrated/rfc-0099-dot-separated-module-paths.md` (issue #275). Pattern paths changed from `Type::Variant` to `Type.Variant`.

Type               → IDENTIFIER ( "<" TypeArgs ">" )?
                    | "*"
                    | "()"
                    | "(" Type ( "," Type )+ ")"                // tuple type
                    | Type "[]"                                  // array shorthand
                    | "[" Type ";" INT "]"                       // fixed-size array type (since v0.19.0; RFC-0053)
                    | "(" TypeList? ")" "->" Type               // function / closure type
                    | "extend" Type                               // anonymous bounded param; parameter position only (since v0.7.0; RFC-0035)
                                                                // NOT valid in return position, struct fields, or type aliases — see RFC-0037, RFC-0038
TypeArgs           → Type ( "," Type )*
TypeList           → Type ( "," Type )*
```
