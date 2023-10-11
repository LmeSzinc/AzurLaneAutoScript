function string.split(s, p)
    local Result= {}
    string.gsub(s, '[^'..p..']+', function(w) table.insert(Result, w) end)
    return Result
end

function ChangeShip()
    local Result = gg.prompt({"舰船Id", "舰船星级", "当前舰种Id", "目标舰种Id"}
			 		    	,{} 
			 		    	,{"number", "number", "number", "number"})

	local ShipIdList = string.split(tostring(Result[1]), ";")
	local ShipStarList = string.split(tostring(Result[2]), ";")
	local ShipTypeIdList = string.split(tostring(Result[3]), ";")
	local TargetShipTypeIdList = string.split(tostring(Result[4]), ";")

	if #ShipIdList ~= #ShipTypeIdList or #ShipIdList ~= #TargetShipTypeIdList or #ShipIdList ~= #ShipStarList then
		Exit("参数数量不匹配！")
	end

	for i = 1, #ShipIdList do
		gg.searchNumber(ShipIdList[i]..";"..ShipStarList[i]..";"..ShipTypeIdList[i].."::610", gg.TYPE_DOUBLE)
		gg.refineNumber(ShipTypeIdList[i], gg.TYPE_DOUBLE)
		local SearchResult =  gg.getResults(1024)
		if next(SearchResult) == nil then
			gg.clearResults()
			gg.searchNumber(ShipIdList[i]..";"..ShipStarList[i]..";"..ShipTypeIdList[i].."::610", gg.TYPE_DWORD)
		    gg.refineNumber(ShipTypeIdList[i], gg.TYPE_DWORD)
		    gg.getResults(1024)
			gg.editAll(TargetShipTypeIdList[i], gg.TYPE_DWORD)
		else
			gg.editAll(TargetShipTypeIdList[i], gg.TYPE_DOUBLE)
		end
		gg.clearResults()
	end
	Exit("修改成功！")
end 

function Exit(Message)
    gg.alert(Message)
	os.exit()
end

function Main()
	Choice = gg.choice({
        "改船",
		"退出",
	}, nil, nil)
	if Choice == 1 then
		ChangeShip()
	end
	if Choice == 2 then
		Exit("退出成功！")
	end
	FX=false
end

gg.clearResults()
Main()