CREATE TABLE IF NOT EXISTS Guild ( 
	id                   INTEGER NOT NULL  PRIMARY KEY  ,
	timezone             TEXT
 );

CREATE TABLE IF NOT EXISTS Member_time_role ( 
	id                   INTEGER NOT NULL    ,
	creation_time        timestamp NOT NULL  ,
	deltatime            TIME NOT NULL    ,
	member_id            INTEGER NOT NULL    ,
	guild_id             INTEGER NOT NULL    ,
	CONSTRAINT pk_Member_time_role PRIMARY KEY ( id, member_id, guild_id ),
	FOREIGN KEY ( guild_id ) REFERENCES Guild( id ) ON DELETE CASCADE 
 );

CREATE TABLE IF NOT EXISTS Time_role ( 
	id                   INTEGER NOT NULL    ,
	guild_id             INTEGER NOT NULL    ,
	deltatime            TIME NOT NULL    ,
	CONSTRAINT pk_Time_role PRIMARY KEY ( id, guild_id ),
	FOREIGN KEY ( guild_id ) REFERENCES Guild( id )  ON DELETE CASCADE
 );

CREATE TABLE IF NOT EXISTS Global_time_role ( 
	id                   INTEGER NOT NULL    ,
	end_datetime         timestamp NOT NULL    ,
	guild_id             INTEGER NOT NULL    ,
	delete_from_guild    BOOLEAN NOT NULL    ,
	CONSTRAINT pk_Global_time_role PRIMARY KEY ( id, guild_id ),
	FOREIGN KEY ( guild_id ) REFERENCES Guild( id ) ON DELETE CASCADE 
 );