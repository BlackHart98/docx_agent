# DOCX Agent
*AI agent API for the assessment of DOCX legal contract using track changes and comments*


## Overview
Docx_agent parses legal contracts `.docx` file gets track changes and comments, then returns a revision analysis

## Prerequisites
1. Install [docker](https://docs.docker.com/get-started/get-docker/)
2. Install Python3 (python 3.11+ preferably)

## How to use this
1. Create a `.env` file to keep your credentials, which are
```env
MISTRAL_AI_KEY=
OPEN_AI_KEY=
POSTGRES_USERNANME=
POSTGRES_PASSWORD=
POSTGRES_DB=
```
> [!Note]
> I am currently using Mistral API

2. Create a virtual environment 
```sh
python -m venv env
```
then activate the virtual environment, by running this 
> for unix-based systems (linux and macOS)
```sh
source activate
```