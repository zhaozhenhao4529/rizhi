# 日知

天猫 AI 黑客松 · 高校挑战赛 · 赛道「智能日常」。

手机自己知道今天要过什么样的一天：早晨出门卡、白天随手一拍、晚上一日页。没有大模型 Key 时用本地规则，演示不会中断。

## 跑起来

需要 Python 3.10+。改前端时再装 Node.js 18+。

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

浏览器打开 http://127.0.0.1:8000

仓库里已经带好示例衣橱和抠好的衣服图。想清空后重做种子数据：删掉 `backend/wardrobe.db`，再在 `backend` 目录执行 `python3 seed.py`。

## 改界面

```bash
cd frontend
npm install
npm run dev
```

开发服务器在 http://127.0.0.1:5173 ，会把 `/api` 和 `/uploads` 代理到 8000 端口。改完要给别人看打包结果时：

```bash
npm run build
```

然后重新打开 8000 端口的页面。

## 接上 Qwen

```bash
export DASHSCOPE_API_KEY=你的百炼Key
```

再启动后端。识衣、搭配和读图会走 Qwen / Qwen-VL。不设置则使用本地规则。

## 一起改

页面在 `frontend/src`，接口在 `backend/main.py`，搭配和读图在 `backend/ai_service.py`。
