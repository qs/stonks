import os
import io
import base64
from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import requests
from mistralai import Mistral

app = FastAPI()
templates = Jinja2Templates(directory="templates")

CHART_IMG_API_KEY = os.environ.get("CHART_IMG_API_KEY")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

model = "pixtral-12b-2409"
mistral_client = Mistral(api_key=MISTRAL_API_KEY)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze")
async def analyze_stock(ticker: str = Form(...)):
    # Fetch chart image
    print(f"Fetching chart image for {ticker}")
    chart_response = requests.post(
        "https://api.chart-img.com/v2/tradingview/advanced-chart",
        headers={
            "x-api-key": CHART_IMG_API_KEY,
            "content-type": "application/json",
        },
        json={
            "height": 500,
            "theme": "dark",
            "interval": "15m",
            "session": "extended",
            "symbol": f"COINBASE:{ticker}",
            "timezone": "America/New_York",
            "studies": [
                {
                    "name": "Bollinger Bands",
                    "input": {
                        "length": 20,
                        "stdDev": 2
                    }
                },
                {
                "name": "Fisher Transform",
                "forceOverlay": False,
                "input": {
                    "in_0": 9
                },
                "override": {
                    "Fisher.visible": True,
                    "Fisher.linewidth": 1,
                    "Fisher.plottype": "line",
                    "Fisher.color": "rgb(33,150,243)",
                    "Trigger.visible": True,
                    "Trigger.linewidth": 1,
                    "Trigger.plottype": "line",
                    "Trigger.color": "rgb(255,109,0)",
                    "Level0.visible": True,
                    "Level0.linestyle": 2,
                    "Level0.linewidth": 1,
                    "Level0.value": 1.5,
                    "Level0.color": "rgb(233,30,99)",
                    "Level1.visible": True,
                    "Level1.linestyle": 2,
                    "Level1.linewidth": 1,
                    "Level1.value": 0.75,
                    "Level1.color": "rgb(120,123,134)",
                    "Level2.visible": True,
                    "Level2.linestyle": 2,
                    "Level2.linewidth": 1,
                    "Level2.value": 0,
                    "Level2.color": "rgb(233,30,99)",
                    "Level3.visible": True,
                    "Level3.linestyle": 2,
                    "Level3.linewidth": 1,
                    "Level3.value": -0.75,
                    "Level3.color": "rgb(120,123,134)",
                    "Level4.visible": True,
                    "Level4.linestyle": 2,
                    "Level4.linewidth": 1,
                    "Level4.value": -1.5,
                    "Level4.color": "rgb(233,30,99)"
                }
                },
                {
                    "name": "Moving Average",
                    "input": {
                        "length": 9,
                        "source": "close",
                        "offset": 0,
                        "smoothingLine": "SMA",
                        "smoothingLength": 9
                    },
                    "override": {
                        "Plot.linewidth": 1,
                        "Plot.plottype": "line",
                        "Plot.color": "rgb(33,150,243)"
                    }
                }
            ]
        },
    )

    chart_image = chart_response.content
    print(f"Chart image fetched: {chart_response.status_code}")
    encoded_image = base64.b64encode(chart_image).decode('utf-8')
    with open("chart.png", "wb") as f:
        f.write(chart_image)

    # Analyze the chart using Mistral
    chat_response = mistral_client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Give a detailed technical analysis, mentioning common signals. Pay special attention to the Bollinger Bands, Moving Average, and Fisher Transform indicators visible in the chart. And as the last point in the summary tell whether that technical analysis strategy would have made maoney over past year or not and how much in %. Always include an example back testing result"
                    },
                    {
                        "type": "image_url",
                        "image_url": f"data:image/png;base64,{encoded_image}"
                    }
                ]
            },
        ]
    )

    analysis = chat_response.choices[0].message.content
    print(analysis)
    return {
        "chart_image": f"data:image/png;base64,{encoded_image}",
        "analysis": analysis,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
