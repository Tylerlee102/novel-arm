typedef unsigned long u64;

static long sys_write(int fd, const void *buf, u64 len)
{
    register u64 x0 __asm__("x0") = (u64)fd;
    register const void *x1 __asm__("x1") = buf;
    register u64 x2 __asm__("x2") = len;
    register u64 x8 __asm__("x8") = 64;
    __asm__ volatile("svc #0" : "+r"(x0) : "r"(x1), "r"(x2), "r"(x8) : "memory");
    return (long)x0;
}

static void sys_exit(int code)
{
    register u64 x0 __asm__("x0") = (u64)code;
    register u64 x8 __asm__("x8") = 93;
    __asm__ volatile("svc #0" : : "r"(x0), "r"(x8) : "memory");
    __builtin_unreachable();
}

void _start(void)
{
    static const char msg[] = "AARCH64_CLANG_SMOKE_OK\n";
    sys_write(1, msg, sizeof(msg) - 1);
    sys_exit(0);
}
