template <typename T> class Box {};
template class Box<int>;
template <typename T> void run(T) {}
template void run<int>(int);
