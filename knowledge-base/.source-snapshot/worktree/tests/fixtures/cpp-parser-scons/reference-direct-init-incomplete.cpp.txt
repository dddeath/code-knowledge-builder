struct T { explicit T(int); };
void bind_reference() {
    int expr = 1;
    const T &x(;
}
