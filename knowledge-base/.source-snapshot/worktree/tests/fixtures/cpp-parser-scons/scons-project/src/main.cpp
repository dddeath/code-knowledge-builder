#ifndef NDEBUG
template <typename T> class Box {};
template class Box<int>;
#endif

int public_service(int value) {
    return value + 1;
}
