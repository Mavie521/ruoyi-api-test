with open("perf_users.csv", "w", encoding="utf-8") as f:
    f.write("username,password\n")
    # for 向内缩进，放在with块里面，文件保持打开状态
    for i in range(1, 201):
        f.write(f"loaduser_{i:06d},perf12345\n")