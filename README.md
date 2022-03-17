# Trade-bot-upbit V6.0
트레일링 형식의 업비트용 트레이딩 봇입니다. 코드의 최적화 및 디자인패턴, 알고리즘 문제가 있어 개발을 진행하지 않습니다.

<div align = "center">
  <span style = "color: red;">Warning: 자동투자 매매는 큰 손실을 유발할 수 있습니다.</span>
</div>

## Features
- 설정한 차트라인 주기에 따라 이전 봉차트의 변동폭에 특정 K값을 곱한 만큼 올라가면 매수, 내려가면 매도를 진행합니다.
- 최적의 k값은 백테스팅을 통해 자동 연산합니다.
- 매수는 이동평균선위에 위치했을 때만 진행합니다.
- 업비트 API를 사용하여 사용자의 자산이 설정한 금액보다 낮을 경우 거래가 중지됩니다.
- 현재금액, 상승장, 하락장 등의 정보를 표시합니다.
- 현재 매수한 자산을 표시합니다.

## Installation
```
pip install colorama
pip install openpyxl
pip install deprecated
pip install pyupbit
pip install PyQt5
```
or if your computer OS is Windows **run to 'install.bat'**

## How to work
![image](https://user-images.githubusercontent.com/90737528/158761719-6c658170-85d1-4c6f-b001-e17fad950236.png)

## Demo
~~None~~


## Snapshots
![image](https://user-images.githubusercontent.com/90737528/158436122-2f821f94-859c-4e76-a7fc-bb6dfa846bf4.png)
----
| #Photo1 | #Photo2 |  
| :-: | :-: |
| <img src="https://user-images.githubusercontent.com/90737528/158442222-6c246c4c-d1a4-4071-8629-e8ba45b2eb23.png"/> | <img src="https://user-images.githubusercontent.com/90737528/158442239-176ddfbf-4b05-4e4b-9b15-ba9c468e06b8.png"/> |
| #Photo3 | #Photo4 |  
| <img src="https://user-images.githubusercontent.com/90737528/158442257-a1e7ba84-d32c-4bbd-a1b9-a417727e8bd1.png"/>| <img src="https://user-images.githubusercontent.com/90737528/158442275-39e28a73-f6f9-45c9-acef-b1a826cca2a0.png"/> |

## How to use   
- Run 'install.bat' if you want to install associated python library.
- Please enter the your Upbit API Key in the blank
- Click to '최적화' button

## Thanks
~~None~~

## License
```
MIT License

Copyright (c) 2022 harusiku

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```


