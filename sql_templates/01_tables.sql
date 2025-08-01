IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'FootballMatches' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
CREATE TABLE FootballMatches (
    [MatchID] BIGINT IDENTITY(1,1) PRIMARY KEY,
    [Division] VARCHAR(2) NULL, -- Name of the division.
    [MatchDate] DATE NULL, -- Enclosed in brackets as 'Date' is a SQL keyword
    [MatchTime] TIME(0) NULL, -- Enclosed in brackets as 'Time' is a SQL keyword
    [HomeTeam] VARCHAR(100) NULL, -- Name of the home team.
    [AwayTeam] VARCHAR(100) NULL, --Name of the away team.
    [FTHG] INT NULL, -- Full Time Home Goals (target variable or feature for goal difference).
    [FTAG] INT NULL, -- Full Time Away Goals (target variable or feature for goal difference).
    [FTR] CHAR(1) NULL, -- Full Time Result (H=Home Win, D=Draw, A=Away Win - often the primary target variable).
    [HTHG] INT NULL, -- Half Time Home Goals.
    [HTAG] INT NULL, -- Half Time Away Goals.
    [HTR] CHAR(1) NULL, -- Half Time Result.
    [HS] INT NULL, -- Home Shots.
    [AS] INT NULL, -- Away Shots.
    [HST] INT NULL, -- Home Shots on Target.
    [AST] INT NULL, -- Away Shots on Target.
    [HF] INT NULL, -- Home Fouls.
    [AF] INT NULL, -- Away Fouls.
    [HC] INT NULL, -- Home Corners.
    [AC] INT NULL, -- Away Corners.
    [HY] INT NULL, -- Home Yellow Cards.
    [AY] INT NULL, -- Away Yellow Cards.
    [HR] INT NULL, -- Home Red Cards.
    [AR] INT NULL, -- Away Red Cards.
    [AvgH] FLOAT NULL, -- Average odds for Home Win (pre-match).
    [AvgD] FLOAT NULL, -- Average odds for Draw (pre-match).
    [AvgA] FLOAT NULL, -- Average odds for Away Win (pre-match).
    [Avg_Over_2_5] FLOAT NULL, -- Average odds for Over 2.5 Goals (pre-match).'
    [Avg_Under_2_5] FLOAT NULL, -- Average odds for Under 2.5 Goals (pre-match).
    [AvgAHH] FLOAT NULL, -- Average Asian Handicap Home Odds (pre-match).
    [AvgAHA] FLOAT NULL, -- Average Asian Handicap Away Odds (pre-match).
    [AvgCH] FLOAT NULL, -- Average closing odds for Home Win.
    [AvgCD] FLOAT NULL, -- Average closing odds for Draw.
    [AvgCA] FLOAT NULL, -- Average closing odds for Away Win.
    [AvgC_Over_2_5] FLOAT NULL, -- Average closing odds for Over 2.5 Goals.
    [AvgC_Under_2_5] FLOAT NULL, -- Average closing odds for Under 2.5 Goals.
    [AvgCAHH] FLOAT NULL, -- Average closing Asian Handicap Home Odds.
    [AvgCAHA] FLOAT NULL -- Average closing Asian Handicap Away Odds.
);
END;