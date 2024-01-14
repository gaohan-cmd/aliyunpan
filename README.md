# aliyunpan
阿里云盘每日签到
# 使用教程
  1、打开青龙面板，脚本管理-》新建空文件夹（文件名aliyunpan，父目录为空）-》新建空文件（文件名autosign.py，父目录aliyunpan)
  
  2、依赖管理-》添加python依赖
  
  3、定时任务-》添加任务（命令：	/ql/data/scripts/aliyunpan/autosign.py 定时规则：0 9 * * *）
  
  4、环境变量-》新建变量（新建一个变量，名称为：aliyunpan_refresh_token）
  
  5、定时任务-》执行（查看日志是否成功）
# aliyunpan_refresh_token获取
获取阿里云盘refresh_token, 打开浏览器，登录[阿里云盘](https://www.aliyundrive.com/) 打开控制台DevTools(快捷键F12) -> 控制台输入JSON.parse(localStorage.getItem("token")).refresh_token，复制 refresh_token
![image](https://github.com/gaohan-cmd/aliyunpan/assets/63499259/c114063c-2016-4ff0-a957-8394afdb13bb)


