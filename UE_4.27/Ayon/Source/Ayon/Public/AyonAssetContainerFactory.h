// Copyright (c) 2023 Ynput s.r.o.
#pragma once

#include "CoreMinimal.h"
#include "Factories/Factory.h"
#include "AyonAssetContainerFactory.generated.h"

/**
 * 
 */
UCLASS()
class AYON_API UAyonAssetContainerFactory : public UFactory
{
	GENERATED_BODY()

public:
	UAyonAssetContainerFactory(const FObjectInitializer& ObjectInitializer);
	virtual UObject* FactoryCreateNew(UClass* Class, UObject* InParent, FName Name, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn) override;
	virtual bool ShouldShowInNewMenu() const override;
};