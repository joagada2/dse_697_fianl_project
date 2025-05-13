## UTKAsk:CONVERSATIONAL RAG AGENT FOR WEB CONTENT INTERACTION AND NAVIGATION

## INTRODUCTION/MOTIVATION
LLMs are increasingly becoming preferred option for accessing publicly available information through natural language interface. LLMs exceed expectation  excel in language tasks but they are parametric models whose responses are based on probability and hence prone to hallucination. Also, LLMs are purged of updated knowledge due to their knowledge cut off on the day they are trained. With this, LLM is not a good option for website visitors from countries around the world search around the over 19,000 url from both the main domain and sub domain of UTK website. In this project, we build a RAG system that will help UTK Website visitors to interact with information on UTK website through a web interface. To achieve this, we craw the utk.edu and scraped 19526 urls, build and retrieval system with the data so that the generator which is an LLM generate response only based on context provided from the knowledge base.
## PROJECT OBJECTIVE
There are over 19,000 pages from the main domain and sub-domain of the UTK website (utk.edu). Visitors from around the world scan through pages of this website every day looking from desired information. Most time, people need just a sentence to get the right information, but they had to scan through pages and read irrelevant content to get the information they need. The objective of this project is to build a RAG based chatbot through which website visitors can access information from the website without having to scan through different pages or reading irrelevant contents.
## PROJECT WORKFLOW
 - We write a script that takes a URL to the home page of a website and details of prefereed NOSQL Database (DynamoDB in our case), extract all URLs from the domain and subdomains (No link to external websites), extract all text data from the web pages and save in the chosed database. We used this script to extract texts from 19,526 URLs on UTK website
 - The we pulled the data from the database, converted each page into a seperate chunk, tokenize the chunk, embed with the lopen ai embedding model, index the vectors and store in pinecone database
 - We Build a FastAPI backend that fetches query, tokenize and embed the query, take that to the pinecone database, pick the top k index with the highest cosine similarity, build a more comprehensive propmt with the query and thr retrived knowledge, then take the prompt to the LLM to get generate response.
 - The response is passed to the user and stored in a Redis database. When the user sends another query, the query is combined with all previois query in the Redis database and sent for tokenization embedding and then to pinecone database to pick related index and repeat the same steps.
 - The frontend was build with React to prvide friendly interface for users
 - The backend (FastAPI) was containerized and deployed deployed on AWS EC2 Server
 - Frontend was also build and deployed to another EC2 Server
 - The deployment profess was automated using GitHub Action CI/CD Pipeline
## TOOLS USED IN THIS PROJECT
 - Programming Language - Python
 - Vector Embedding – Open Ai
 - Vector Database – Pinecone​
 - Backend – FastAPI
 - Frontend – React​
 - Web crawling and scrapping – Beautiful Soup and Playwright​
 - NoSQL Database – DynamoDB​
 - Workflow Orchestration – Prefect​
 - Cloud Serve - AWS EC2
 - Query Cache Storage - Redis
 - Rendering of Webpage - Nginx
 - COntainerization - Docker
 - CI/CD - Github Action
## WORKFLOW DIAGRAM/RAG ARCHITECTURE
 - 
![image](https://github.com/user-attachments/assets/11cbe63c-3afc-4ea1-b6b3-aee478c916c8)

## RESULT
The result for this project is an end to end RAG application we called UTKAsk
## APPLICATION LINKS
 - Frontend [here](http://3.144.96.138/)
 - Backend [here](http://3.143.23.19:8000/docs)
## How to Run The Project
 - Create a DynamoDB Table and note the table's name
 - Enter the Table in the Webscraper script in the repo
 - Clone this github repo by running <pre> <code> https://github.com/joagada2/dse_697_fianl_project.git </code> </pre> froom the directory where you want to save the code
 - Open the script titles wed_acraper, replace the UTK url with the URL of any website tou want to crawl and scrape and also replace the Dynamo table name with your Dynamo table name and run the script. 
 - After the scrapping is done, run the rag_workflow notebook to extract datafrom Dynamo database, chunk, embed and index in Pinecone. Ensure to have the necessary Pinecone, aws and OpenAI secret keys
 - Now that you have vector vector indexes, also create Redis secret and have the url in your .env. All other secrets shouls be in your .env file too. the run <pre> <code> docker compose --build </code> </pre> and <pre> <code> docker compose --up </code> </pre> to build image and run your container
 - If the app runs successfully, provision AWS EC2, SSH into the server, clone the repository into EC2, install all needed requirements, including Nginx, build the image as above and run the container
 - Provision another EC2 server, deploy the frontend the same way.
 - All the URL for the backend to the frontend
 - All allsecrets to GitHub Action, and configure GitHub Action CI/CD to automate the deployment
