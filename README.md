# JOG-POST

## 이 프로젝트에서 하고자 하는것

이 프로젝트는 strava 로부터 strava api 를 이용하여 사용자의 달리기 기록을 내려받아 해당 데이터를 저장 한 후, 여러가지 형태로 가공하여 활용하고자 하는 프로젝트입니다.

## 이 프로젝트에서 제공하고자 하는 기능
1. 운동 종료 시, strava 로부터 자동으로 달리기 운동기록을 조회한 후 저장할 수 있다.
2. 사용자의 운동 session 별 운동 기록(운동시간, 달린거리, 페이스, 경로 사진 등을) 조회할 수 있다.
3. 사용자의 운동기록을 바탕으로 llm을 연동하여 기록향상을 위한 조언을 받을 수 있다.


## 기술스택

- Back End
  - Python (fastapi)
  - Postgresql
  - uv (의존성 관리)
- Front End
  - vue.js

## 프로젝트 구조

- backend 와 frontend가 하나의 repository 에서 관리되는 mono-repo 구조를 사용하도록 한다.

