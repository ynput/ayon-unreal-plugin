// Copyright (c) 2023 Ynput s.r.o.

#pragma once

#include "CoreMinimal.h"
#include "IWebSocket.h"       // Socket definition

#include "AyonCommunication.generated.h"


USTRUCT()
struct FRpcCall
{
    GENERATED_BODY()

public:
    UPROPERTY()
    FString jsonrpc;

    UPROPERTY()
    FString method;

	UPROPERTY()
	TArray<FString> params;

    UPROPERTY()
    int32 id;
};

USTRUCT()
struct FRpcError
{
    GENERATED_BODY()

public:
    UPROPERTY()
    int32 code;

    UPROPERTY()
    FString message;

	UPROPERTY()
	FString data;
};

USTRUCT()
struct FRpcResponseResult
{
    GENERATED_BODY()

public:
    UPROPERTY()
    FString jsonrpc;

    UPROPERTY()
    FString result;

    UPROPERTY()
    int32 id;
};

USTRUCT()
struct FRpcResponseError
{
    GENERATED_BODY()

public:
    UPROPERTY()
    FString jsonrpc;

	UPROPERTY()
	struct FRpcError error;

    UPROPERTY()
    int32 id;
};

class FAyonCommunication
{
public:
	static void CreateSocket();
	static void ConnectToSocket();
    static void CloseConnection();

	static bool IsConnected();

    static void CallMethod(const FString Method, const TArray<FString> Args);

public:
    UFUNCTION()
    static void OnConnected();

    UFUNCTION()
    static void OnConnectionError(const FString & Error);

    UFUNCTION()
    static void OnClosed(int32 StatusCode, const FString& Reason, bool bWasClean);

    UFUNCTION()
    static void OnMessage(const FString & Message);

    UFUNCTION()
    static void OnMessageSent(const FString& MessageString);

private:
    static void HandleResult(TSharedPtr<FJsonObject> Root);
    static void HandleError(TSharedPtr<FJsonObject> Root);
    static void RunMethod(TSharedPtr<FJsonObject> Root);

private:
	static TSharedPtr<IWebSocket> Socket;
    static int32 Id;
};
