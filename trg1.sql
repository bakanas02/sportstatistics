USE [UFC];
GO

-- Триггер для уведомления о вставке записи в таблицу Fighters
CREATE TRIGGER NotifyInsertFighter
ON Fighters
AFTER INSERT
AS
BEGIN
    PRINT 'Inserted a record into Fighters table';
END;

-- Триггер для уведомления об обновлении записи в таблице Fighters
CREATE TRIGGER NotifyUpdateFighter
ON Fighters
AFTER UPDATE
AS
BEGIN
    PRINT 'Updated a record in Fighters table';
END;

-- Триггер для уведомления об удалении записи из таблицы Fighters
CREATE TRIGGER NotifyDeleteFighter
ON Fighters
AFTER DELETE
AS
BEGIN
    PRINT 'Deleted a record from Fighters table';
END;
