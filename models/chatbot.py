import requests

url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/chat?version=2023-05-29"

body = {
	"messages": [{"role":"system","content":"You always answer the questions with markdown formatting using GitHub syntax. The markdown formatting you support: headings, bold, italic, links, tables, lists, code blocks, and blockquotes. You must omit that you answer the questions with markdown.\n\nAny HTML tags must be wrapped in block quotes, for example ```<html>```. You will be penalized for not rendering code in block quotes.\n\nWhen returning code blocks, specify language.\n\nYou are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. \nYour answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.\n\nIf a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don'\''t know the answer to a question, please don'\''t share false information."}],
	"project_id": "adf0626a-5f99-4f48-b3eb-2f46a450c059",
	"model_id": "meta-llama/llama-3-3-70b-instruct",
	"frequency_penalty": 0,
	"max_tokens": 2000,
	"presence_penalty": 0,
	"temperature": 0,
	"top_p": 1
}

headers = {
	"Accept": "application/json",
	"Content-Type": "application/json",
	"Authorization": "Bearer eyJraWQiOiIyMDE5MDcyNCIsImFsZyI6IlJTMjU2In0.eyJpYW1faWQiOiJJQk1pZC02OTgwMDE0OUZYIiwiaWQiOiJJQk1pZC02OTgwMDE0OUZYIiwicmVhbG1pZCI6IklCTWlkIiwianRpIjoiZGY2ZGE0YjAtNzAwZC00Mzk0LWI2NDMtNzJkZTIwM2YwOWI1IiwiaWRlbnRpZmllciI6IjY5ODAwMTQ5RlgiLCJnaXZlbl9uYW1lIjoiQnJpYW4iLCJmYW1pbHlfbmFtZSI6Ik91IiwibmFtZSI6IkJyaWFuIE91IiwiZW1haWwiOiJicmlhbm91N0BnbWFpbC5jb20iLCJzdWIiOiJicmlhbm91N0BnbWFpbC5jb20iLCJhdXRobiI6eyJzdWIiOiJicmlhbm91N0BnbWFpbC5jb20iLCJpYW1faWQiOiJJQk1pZC02OTgwMDE0OUZYIiwibmFtZSI6IkJyaWFuIE91IiwiZ2l2ZW5fbmFtZSI6IkJyaWFuIiwiZmFtaWx5X25hbWUiOiJPdSIsImVtYWlsIjoiYnJpYW5vdTdAZ21haWwuY29tIn0sImFjY291bnQiOnsidmFsaWQiOnRydWUsImJzcyI6ImJiZDhlYzU4MjFiMTQ1YWY4MzAwYjc2MzAzMzM1ZTQyIiwiaW1zX3VzZXJfaWQiOiIxNDU0NDg0NSIsImZyb3plbiI6dHJ1ZSwiaW1zIjoiMzEyODMwMyJ9LCJtZmEiOnsiaW1zIjp0cnVlfSwiaWF0IjoxNzYyNTYwMzM1LCJleHAiOjE3NjI1NjM5MzUsImlzcyI6Imh0dHBzOi8vaWFtLmNsb3VkLmlibS5jb20vaWRlbnRpdHkiLCJncmFudF90eXBlIjoidXJuOmlibTpwYXJhbXM6b2F1dGg6Z3JhbnQtdHlwZTphcGlrZXkiLCJzY29wZSI6ImlibSBvcGVuaWQiLCJjbGllbnRfaWQiOiJkZWZhdWx0IiwiYWNyIjoxLCJhbXIiOlsicHdkIl19.sWoWap9CQhThrdDM685kdpTJCBZyFIVlLtbMWOuT_ORpq7sW6idqHbuNggkTyodigcRS0sWkiSSf81xYFTZ-rlSJI3zNGYo2uQiEIYITplMIHNXrAlmVhjDVDcAwYe7-RYmP9gixvc1US-E19blcI76LfLX1HiA8cbbvwBDWGZaBYsk1vnJxy5S1ovuXEHdFyq73I8fB_M0PmJR9ptScMmBriayMRvzoocX9r1w_vXK22YrrJ7TR3DzTCvtBFXUeDazPmqUkcgDcBwVUxlDBGxEBBkugenFDPdpvNBSJIfoyQjRZR9i0q9ovu41BCDaglDYF4tRpSQrvtgpaBSWxzw"
}

response = requests.post(
	url,
	headers=headers,
	json=body
)

if response.status_code != 200:
	raise Exception("Non-200 response: " + str(response.text))

data = response.json()