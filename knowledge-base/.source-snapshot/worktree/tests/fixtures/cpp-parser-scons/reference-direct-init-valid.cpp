struct T { explicit T(int); };
int source_value();
void bind_reference() {
    int expr = source_value();
    const T &x(expr);
}
