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
                   | MutDeclaration
                   | FunDeclaration
                   | StructDeclaration
                   | EnumDeclaration
                   | ImplBlock
                   | TraitDeclaration
                   | Statement

LetDeclaration     → "let" IDENTIFIER ( ":" Type )? "=" Expression ";"
MutDeclaration     → "mut" IDENTIFIER ( ":" Type )? "=" Expression ";"
FunDeclaration     → NativeBinding? "pub"? "fun" IDENTIFIER GenericParams? "(" Params? ")" ( "->" Type )? WhereClause? ( Block | ";" )
NativeBinding      → "native" "(" "@" IDENTIFIER ( "." IDENTIFIER )* ")"  // standard library only
StructDeclaration  → "pub"? "struct" IDENTIFIER GenericParams? WhereClause? "{" StructFields "}"
EnumDeclaration    → "pub"? "enum" IDENTIFIER GenericParams? WhereClause? "{" EnumVariants "}"
ImplBlock          → "impl" ( Type "for" )? Type "{" FunDeclaration* "}"
TraitDeclaration   → "pub"? "aspect" IDENTIFIER "{" TraitMethod* "}"
TraitMethod        → "fun" IDENTIFIER "(" Params? ")" ( "->" Type )? ( Block | ";" )

Params             → Param ( "," Param )* ","?
Param              → ( "mut" )? "self" | IDENTIFIER ( ":" Type )?
StructFields       → StructField ( "," StructField )* ","?
StructField        → IDENTIFIER ":" Type
EnumVariants       → EnumVariant ( "," EnumVariant )* ","?
EnumVariant        → IDENTIFIER ( "{" StructFields "}" )?
GenericParams      → "<" GenericParam ( "," GenericParam )* ">"
GenericParam       → IDENTIFIER ( ":" BoundList )?                      // since v0.7.0; RFC-0034
BoundList          → Type ( "+" Type )*                                 // since v0.7.0; RFC-0034
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
ForInit             → MutDeclaration | ExpressionStatement | ";"
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
UnaryExpression         → ( "!" | "-" | "*" | "&" | "&mut" ) UnaryExpression | PostfixExpression
PostfixExpression       → PrimaryExpression ( "(" Arguments? ")" | "." IDENTIFIER | "[" Expression "]" | "?" )*
Arguments               → Expression ( "," Expression )* ","?

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

Path               → ( "root" | "std" | "self" | "super" | IDENTIFIER ) ( "::" IDENTIFIER )*

StructLiteral      → Path "{" FieldInit ( "," FieldInit )* ","? "}"
FieldInit          → IDENTIFIER ( ":" Expression )?   // omitting ": Expression" uses the local variable of the same name

MatchExpression    → "match" Expression "{" MatchArm ( "," MatchArm )* ","? "}"
MatchArm           → Pattern ( "if" Expression )? "=>" Expression
IfExpression       → "if" "(" Expression ")" Block "else" Block
LoopExpression     → "loop" Block
ClosureExpression  → "(" Params? ")" ( "->" Type )? Block

Pattern            → "_"
                   | "None"
                   | IDENTIFIER
                   | "(" Pattern ( "," Pattern )* ")"          // tuple pattern
                   | IDENTIFIER "::" IDENTIFIER ( "{" PatternFields "}" )?
                   | INT | FLOAT | STRING | "true" | "false"
PatternFields      → IDENTIFIER ( "," IDENTIFIER )*

Type               → IDENTIFIER ( "<" TypeArgs ">" )?
                   | "*" "mut"? Type                           // regular pointer types
                   | "()"
                   | "(" Type ( "," Type )+ ")"                // tuple type
                   | Type "[]"                                  // array shorthand
                   | "[" Type ";" INT "]"                       // fixed-size array type (since v0.19.0; RFC-0053)
                   | "(" TypeList? ")" "->" Type               // function / closure type
                   | "impl" Type                               // anonymous bounded param; parameter position only (since v0.7.0; RFC-0035)
                                                               // NOT valid in return position, struct fields, or type aliases — see RFC-0037, RFC-0038
TypeArgs           → Type ( "," Type )*
TypeList           → Type ( "," Type )*
```
