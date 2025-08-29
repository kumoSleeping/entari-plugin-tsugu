# entari-plugin-tsugu

一个用于 Entari 框架的 Tsugu BanGDream Bot 插件.

## 安装

```bash
pip install entari-plugin-tsugu
```

## 配置项

`qq_passive`   
此项设置用于 QQ 官方机器人平台驱动器例如[GlycCat](https://github.com/WindowsSov8forUs/GlycCat) 的被动消息支持, 默认为布尔值 `False` 

`prefix`   
此项设置用于命令前缀配置, 默认为 `['/', '']`   
请记住, 如果需要无前缀触发一定要在最后加上空字符串

`platform`   
此项设置用于指定平台，默认为 `None` 时自动检测驱动器返回的平台信息  
请注意: 如果你获取到的 `user.id` 为 QQ号, 将此值设置为 `red` 以共享数据.


> 例如: 你是一个 普通的使用 `napcat` / `Lagrange` 等驱动器的用户, 请保持 `prefix` 与 `qq_passive` 默认配置, 将 `platform` 设置为 `red` 是一个合理的选择.


## Tsugu 配置

Tsugu 内部配置建议使用 `.env` 文件配置, 在命令行使用:
```bash
tsugu -e 
```
以查看支持修改的配置项.