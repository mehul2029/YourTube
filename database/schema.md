**SQL**


*userdb*

userinfo

|user_id | videoid | latest_timestamp | viewCount | like | dislike |
|:------:|:-------:|:----------------:|:---------:|:----:|:-------:|
|		 |	 	   |                  | 		  |      |         |
|		 |		   |                  | 		  |      |         |
|		 |		   |                  | 	      |      |         |


usercred

|user_id | password |
|:------:|:--------:|
|        |          |
|        |          |
|        |          |


**MONGODB**


*comments*

{
	
	videoid: ......,
	
	{
	
		comments: [
	
		{by=user1 , time=2017-01-01, comment-"sample comment"},
	
		{by=user2 , time=2017-01-01, comment-"sample comment"},
	
		]
	
	}

}


*videoInfo*

Provided json data.


*historytags*

{
	
	user_id: ......,
	
	{
	
		tags: [
	
		{tag="manchester", count=4},
	
		{tag="shaolin", count=7},
	
		]
	
	}

}


**NEO4J**

*Relationship graph*
