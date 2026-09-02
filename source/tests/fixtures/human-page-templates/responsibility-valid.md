# 会话检索职责

## 职责概述

负责同一会话内检索进程的创建、复用和释放。

## 什么时候需要修改

会话生命周期事件变化时修改。

## 关键实现

- `start_session`

## 验证入口

- [打开源码：session_stdio.py](vscode://file/E:/fixture/session_stdio.py:1:1)

## 适用边界

只覆盖本地会话检索进程。
