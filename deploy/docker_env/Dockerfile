FROM ubuntu:20.04

# 设置时区以避免交互式提示
ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED 1

# 使用阿里云镜像源替换默认源
RUN sed -i 's/archive.ubuntu.com/repo.huaweicloud.com/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/repo.huaweicloud.com/g' /etc/apt/sources.list && \
    # 安装必要的软件包
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata && \
    apt-get install -y openssh-server && \
    mkdir /var/run/sshd && \
    echo 'root:123456' | chpasswd && \
    # 允许root密码登录
    sed -ri 's/^#?PermitRootLogin\s+.*/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -ri 's/^#?PasswordAuthentication\s+.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    # 禁用PAM以避免相关错误
    sed -ri 's/^#?UsePAM\s+.*/UsePAM no/' /etc/ssh/sshd_config && \
    mkdir /root/.ssh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 22
# 添加-e参数将日志输出到stderr
CMD ["/usr/sbin/sshd", "-D", "-e"]
