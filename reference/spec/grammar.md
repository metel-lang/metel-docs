# Grammar

```
Program            → HeaderDecl* Declaration* EOF

HeaderDecl         → ImportDecl | ExportDecl

ImportDecl         → "import" ImportPath ";"
ExportDecl         → "export" ImportPath ";"
ImportPath         → PathRoot "::" ImportTree
PathRoot           → "root" | "std" | "self" | "super" | IDENTIFIER
ImportTree         → ImportItem
                   | IDENTIFIER "::" ImportTree
                   | "{" ImportItem ( "," ImportItem )* ","? "}"
                   | "*"
ImportItem         → IDENTIFIER ( "as" IDENTIFIER )?

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
NativeBinding      → "native" "(" "@" IDENTIFIER ( "." IDENTIFIER )* ")"
StructDeclaration  → "public"? "struct" IDENTIFIER GenericParams? WhereClause? "{" StructFields "}"
EnumDeclaration    → "public"? "enum" IDENTIFIER GenericParams? WhereClause? "{" EnumVariants "}"
ExtendBlock        → "extend" GenericParams? Type ( ":" ExtendAspectList )? WhereClause? ( "{" ( FunDeclaration | AssocTypeDef )* "}" | ";" )
AspectDeclaration  → "public"? "aspect" IDENTIFIER GenericParams? ( "{" ( AssocTypeDecl | AspectMethod )* "}" | ";" )
AspectMethod       → "fun" IDENTIFIER "(" Params? ")" ( "->" Type )? ( Block | ";" )
ExtendAspectList   → Bound ( "," Bound )*
AssocTypeDef       → "type" IDENTIFIER ( "=" Type )? ";"
AssocTypeDecl      → "type" IDENTIFIER ( ":" BoundList )? ";"

Params             → Param ( "," Param )* ","?
Param              → "self" | "&self" | "&var self" | IDENTIFIER ( ":" Type )?
StructFields       → StructField ( "," StructField )* ","?
StructField        → "public"? IDENTIFIER ":" Type
EnumVariants       → EnumVariant ( "," EnumVariant )* ","?
EnumVariant        → IDENTIFIER ( "{" StructFields "}" )?
GenericParams      → "<" GenericParam ( "," GenericParam )* ">"
GenericParam       → IDENTIFIER ( ":" BoundList )?
BoundList          → Bound ( "+" Bound )*
Bound              → "!"? BoundHead
BoundHead          → IDENTIFIER ( "<" TypeArgs ">" )? | "(" TypeList? ")" "->" Type
WhereClause        → "where" WhereConstraint ( "," WhereConstraint )*
WhereConstraint    → IDENTIFIER ":" BoundList

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
PostfixExpression       → PrimaryExpression ( "(" Arguments? ")" | "." IDENTIFIER | "[" Expression "]" | "?" )*
Arguments               → Expression ( "," Expression )* ","?

PrimaryExpression  → INT | FLOAT | STRING | "true" | "false" | "None" | "()"
                   | "(" Expression ( "," Expression )+ ")"
                   | "(" Expression ")"
                   | "[" ( Expression ( "," Expression )* ","? )? "]"
                   | "[" Expression ";" INT "]"
                   | Path
                   | StructLiteral
                   | MatchExpression
                   | IfExpression
                   | LoopExpression
                   | ClosureExpression

Path               → ( "root" | "std" | "self" | "super" | IDENTIFIER ) ( "::" IDENTIFIER )*
StructLiteral      → Path "{" FieldInit ( "," FieldInit )* ","? "}"
FieldInit          → IDENTIFIER ( ":" Expression )?

MatchExpression    → "match" Expression "{" MatchArm ( "," MatchArm )* ","? "}"
MatchArm           → Pattern ( "if" Expression )? "=>" Expression
IfExpression       → "if" "(" Expression ")" Block "else" Block
LoopExpression     → "loop" Block
ClosureExpression  → "(" Params? ")" ( "->" Type )? Block

Pattern            → "_"
                   | "None"
                   | IDENTIFIER
                   | "(" Pattern ( "," Pattern )* ")"
                   | IDENTIFIER "::" IDENTIFIER ( "{" PatternFields "}" )?
                   | INT | FLOAT | STRING | "true" | "false"
PatternFields      → IDENTIFIER ( "," IDENTIFIER )*

Type               → IDENTIFIER ( "<" TypeArgs ">" )?
                   | "&" Type
                   | "&var" Type
                   | "()"
                   | "(" Type ( "," Type )+ ")"
                   | Type "[]"
                   | "[" Type ";" INT "]"
                   | "(" TypeList? ")" "->" Type
                   | "impl" Type
TypeArgs           → Type ( "," Type )*
TypeList           → Type ( "," Type )*
```

> *Planned for a future minor release (RFC-0098/RFC-0102/RFC-0103).* Impl blocks
> rename to `extend`, mutable bindings rename to `var`, empty `extend` blocks may be
> written with `;`, and empty aspect declarations may be written as `aspect Name;`.
