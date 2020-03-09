Create Table Artists
(
id int PRIMARY KEY IDENTITY (1,1),
first_name VARCHAR(20) not null,
last_name varchar(20) not NULL,
alias varchar(20),
birth_date DATETIME
);

Create Table Albums
(
id int primary key identity(1,1),
name varchar(50 not null,
get rich or die trying
release_date datetime
)

Alter Table Albums ADD
fk_artist_id int foreign key references Artists(id) 
on delete cascade;