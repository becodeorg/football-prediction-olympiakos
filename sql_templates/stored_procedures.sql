IF OBJECT_ID('dbo.UpsertFootballMatches', 'P') IS NOT NULL
    DROP PROCEDURE dbo.UpsertFootballMatches;
GO

CREATE PROCEDURE dbo.UpsertFootballMatches
    @jsonData NVARCHAR(MAX)
AS
BEGIN
    SET NOCOUNT ON;

    -- Declare a table variable to hold the parsed JSON data
    DECLARE @SourceData TABLE (
        Division VARCHAR(2),
        MatchDate DATE,
        MatchTime TIME(0),
        HomeTeam VARCHAR(100),
        AwayTeam VARCHAR(100),
        FTHG INT, FTAG INT, FTR CHAR(1), HTHG INT, HTAG INT, HTR CHAR(1),
        HS INT, [AS] INT, HST INT, AST INT, HF INT, AF INT, HC INT, AC INT, HY INT, AY INT, HR INT, AR INT,
        AvgH FLOAT, AvgD FLOAT, AvgA FLOAT, Avg_Over_2_5 FLOAT, Avg_Under_2_5 FLOAT, AvgAHH FLOAT, AvgAHA FLOAT,
        AvgCH FLOAT, AvgCD FLOAT, AvgCA FLOAT, AvgC_Over_2_5 FLOAT, AvgC_Under_2_5 FLOAT, AvgCAHH FLOAT, AvgCAHA FLOAT
    );

    -- Insert parsed JSON data into the table variable
    INSERT INTO @SourceData (
        Division,MatchDate, MatchTime, HomeTeam, AwayTeam,
        FTHG, FTAG, FTR, HTHG, HTAG, HTR,
        HS, [AS], HST, AST, HF, AF, HC, AC, HY, AY, HR, AR,
        AvgH, AvgD, AvgA, Avg_Over_2_5, Avg_Under_2_5, AvgAHH, AvgAHA,
        AvgCH, AvgCD, AvgCA, AvgC_Over_2_5, AvgC_Under_2_5, AvgCAHH, AvgCAHA
    )
    SELECT
        JSON_VALUE(value, '$.Division'),
        CAST(JSON_VALUE(value, '$.MatchDate') AS DATE),
        CAST(JSON_VALUE(value, '$.MatchTime') AS TIME(0)),
        JSON_VALUE(value, '$.HomeTeam'),
        JSON_VALUE(value, '$.AwayTeam'),
        CAST(JSON_VALUE(value, '$.FTHG') AS INT),
        CAST(JSON_VALUE(value, '$.FTAG') AS INT),
        JSON_VALUE(value, '$.FTR'),
        CAST(JSON_VALUE(value, '$.HTHG') AS INT),
        CAST(JSON_VALUE(value, '$.HTAG') AS INT),
        JSON_VALUE(value, '$.HTR'),
        CAST(JSON_VALUE(value, '$.HS') AS INT),
        CAST(JSON_VALUE(value, '$.AS') AS INT),
        CAST(JSON_VALUE(value, '$.HST') AS INT),
        CAST(JSON_VALUE(value, '$.AST') AS INT),
        CAST(JSON_VALUE(value, '$.HF') AS INT),
        CAST(JSON_VALUE(value, '$.AF') AS INT),
        CAST(JSON_VALUE(value, '$.HC') AS INT),
        CAST(JSON_VALUE(value, '$.AC') AS INT),
        CAST(JSON_VALUE(value, '$.HY') AS INT),
        CAST(JSON_VALUE(value, '$.AY') AS INT),
        CAST(JSON_VALUE(value, '$.HR') AS INT),
        CAST(JSON_VALUE(value, '$.AR') AS INT),
        CAST(JSON_VALUE(value, '$.AvgH') AS FLOAT),
        CAST(JSON_VALUE(value, '$.AvgD') AS FLOAT),
        CAST(JSON_VALUE(value, '$.AvgA') AS FLOAT),
        CAST(JSON_VALUE(value, '$.Avg_Over_2_5') AS FLOAT),
        CAST(JSON_VALUE(value, '$.Avg_Under_2_5') AS FLOAT),
        CAST(JSON_VALUE(value, '$.AvgAHH') AS FLOAT),
        CAST(JSON_VALUE(value, '$.AvgAHA') AS FLOAT),
        CAST(JSON_VALUE(value, '$.AvgCH') AS FLOAT),
        CAST(JSON_VALUE(value, '$.AvgCD') AS FLOAT),
        CAST(JSON_VALUE(value, '$.AvgCA') AS FLOAT),
        CAST(JSON_VALUE(value, '$.AvgC_Over_2_5') AS FLOAT),
        CAST(JSON_VALUE(value, '$.AvgC_Under_2_5') AS FLOAT),
        CAST(JSON_VALUE(value, '$.AvgCAHH') AS FLOAT),
        CAST(JSON_VALUE(value, '$.AvgCAHA') AS FLOAT)
    FROM OPENJSON(@jsonData);

    -- Get total rows from the input JSON
    DECLARE @TotalRows int;
    SELECT @TotalRows = COUNT(*) FROM @SourceData;
    PRINT CONCAT('Total rows received from CSV: ', @TotalRows);

    -- Use MERGE statement to perform conditional inserts
    MERGE dbo.FootballMatches AS Target
    USING @SourceData AS Source
    ON Target.HomeTeam = Source.HomeTeam
    AND Target.AwayTeam = Source.AwayTeam
    AND Target.MatchDate = Source.MatchDate
    AND Target.MatchTime = Source.MatchTime
    WHEN NOT MATCHED THEN
        INSERT (
            [Division],[MatchDate], [MatchTime], [HomeTeam], [AwayTeam],
            [FTHG], [FTAG], [FTR], [HTHG], [HTAG], [HTR],
            [HS], [AS], [HST], [AST], [HF], [AF], [HC], [AC], [HY], [AY], [HR], [AR],
            [AvgH], [AvgD], [AvgA], [Avg_Over_2_5], [Avg_Under_2_5], [AvgAHH], [AvgAHA],
            [AvgCH], [AvgCD], [AvgCA], [AvgC_Over_2_5], [AvgC_Under_2_5], [AvgCAHH], [AvgCAHA]
        )
        VALUES (
            Source.[Division], Source.[MatchDate], Source.[MatchTime], Source.[HomeTeam], Source.[AwayTeam],
            Source.[FTHG], Source.[FTAG], Source.[FTR], Source.[HTHG], Source.[HTAG], Source.[HTR],
            Source.[HS], Source.[AS], Source.[HST], Source.[AST], Source.[HF], Source.[AF], Source.[HC], Source.[AC], Source.[HY], Source.[AY], Source.[HR], Source.[AR],
            Source.[AvgH], Source.[AvgD], Source.[AvgA], Source.[Avg_Over_2_5], Source.[Avg_Under_2_5], Source.[AvgAHH], Source.[AvgAHA],
            Source.[AvgCH], Source.[AvgCD], Source.[AvgCA], Source.[AvgC_Over_2_5], Source.[AvgC_Under_2_5], Source.[AvgCAHH], Source.[AvgCAHA]
        );

    -- Get rows inserted by the MERGE statement
    DECLARE @InsertedRows int;
    SET @InsertedRows = @@ROWCOUNT;
    PRINT CONCAT(@InsertedRows, ' new rows inserted into dbo.FootballMatches.');
    SELECT @InsertedRows AS InsertedRowsCount;
END;
GO
