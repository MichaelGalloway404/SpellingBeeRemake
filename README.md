# Spelling Bee Clone updated with a React front end

This is a reworking of one of my senior projects at EOU while acquiring my BS in Computer Science 
  
This projects stack includes:  
>>Front end using React with vite. 
>>REST API using Pythons Flask library.
>>And MySQL for the database containing 80k words provided by the professor via a word.txt file.
    
Bellow is a tutorial for running the app on a Windows PC.  
  
To run locally on WINDOWS:  
## Step 1:  
>>Download MySQL installer from https://dev.mysql.com/downloads/installer/  
>>Go through installation steps and write down your user name and password  
>>For this project and for the sake of learning I used username = root and password = root but
>>all credentails should be stored in your .env file and imported using dotenv and os.getenv() or another framework is you so choose
>>don't for get to always add your .env to .gitignore file, as to not upload your credentails to your repo -_-

## Step 2:  
>>If added to your environment variables  
>>From command line run the this command:  
>>>>.\mysql.exe -u root -p  
>>Else cd to C:\Program Files\MySQL\MySQL Server 8.0\bin
>>then run .\mysql.exe -u root -p  
  
>>That command should open an SQL command line in the same window  
>>Then from the SQL command line run the this command:  
      
            -- Create database (if you haven't yet)  
            CREATE DATABASE IF NOT EXISTS spellingbee;  
            USE spellingbee;  
            -- Table for valid dictionary words  
            CREATE TABLE valid_words (  
                id INT AUTO_INCREMENT PRIMARY KEY,  
                word VARCHAR(100) UNIQUE NOT NULL  
            );  
  
            -- Table for user sessions and found words  
            CREATE TABLE user_stats (  
                id INT AUTO_INCREMENT PRIMARY KEY,  
                session_id VARCHAR(255) NOT NULL,  
                found_words TEXT, -- will store JSON list of words  
                date_played DATE,  
                UNIQUE (session_id, date_played)  
            );  
>>Or you can use the setup.sql that contains these same lines of code.  
  
## Step 3:  
>>Make sure you have word.txt in the same folder as loadTablesSQL.py  
>>Make sure in loadTablesSQL.py you change the username and password to what you set it in your MySQL install  
>>Run loadTablesSQL.py
   
>>This will fill you DataBase with the 80K+ words from words.txt  
  
## Step 4:  
>>Make sure app.py also has the correct username and password to what you set it in your MySQL install  
  
## Step 5:  
>>cd to spelling-bee-react and run the following command:
>>>>npm run dev

>>This will start our vite server on port 5173
        
## Final step:
>>In the spelling-bee-react folder cd to src
>>Run the following command:
>>>>python app.py
>>Now open a browder and visit the URL http://localhost:5173/  
>>Enjoy the Game!  
