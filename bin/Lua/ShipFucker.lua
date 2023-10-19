function string.split(s, p)
    local Result= {}
    string.gsub(s, '[^'..p..']+', function(w) table.insert(Result, w) end)
    return Result
end
-- 199034;6;3:60>-100;417>-100
-- {Id};{Star};{Type}:{Attribute}>{Target}[;{Attribute}>{Target}...][|{Id};{Star};{Type}:{Attribute}>{Target}[;{Attribute}>{Target}...]]
function ChangeShipAttribute()
    local Result = gg.prompt({"格式：{舰船Id};{舰船星级};{类型Id}:{属性}>{目标值}[;{属性}>{目标值}...]，多个之间用'|'连接"}
			 		    	,{}
			 		    	,{"text"})

	local TargetList = string.split(tostring(Result[1]), "|")
	local OriginalRange = gg.getRanges()
	gg.setRanges(gg.REGION_ANONYMOUS)
    for i = 1, #TargetList do
        local SplitedTarget = string.split(TargetList[i], ":")
        local ShipData = SplitedTarget[1]  -- {Id};{Star};{Type}
        local ShipAttributeList = string.split(SplitedTarget[2], ";")
		--[[
		{
		{Attribute}>{Target},
		{Attribute}>{Target},
		...
		}
		--]]

		gg.searchNumber(ShipData.."::610", gg.TYPE_DOUBLE)
		gg.refineNumber(string.split(ShipData, ";")[1], gg.TYPE_DOUBLE)

		local SearchResult = gg.getResults(1024)

		if next(SearchResult) == nil then
			gg.searchNumber(ShipData.."::610", gg.TYPE_DWORD)
			gg.refineNumber(string.split(ShipData, ";")[1], gg.TYPE_DWORD)
			SearchResult = gg.getResults(1024)
		end

		for j = 1, #SearchResult do
			local MemoryFrom = SearchResult[j].address - 0x1850
			local MemoryTo = SearchResult[j].address
			for k = 1, #ShipAttributeList do
				local SplitedAttribute = string.split(tostring(ShipAttributeList[k]), ">")
				local AttributeToSearchList = SplitedAttribute[1]
				local TargetAttributeList = SplitedAttribute[2]
				gg.clearResults()
				gg.searchNumber(AttributeToSearchList, gg.TYPE_DOUBLE, false, gg.SIGN_EQUAL, MemoryFrom, MemoryTo)
				local AttributeResult = gg.getResults(1024)
				if next(AttributeResult) == nil then
					gg.clearResults()
					gg.searchNumber(AttributeToSearchList, gg.TYPE_DWORD, false, gg.SIGN_EQUAL, MemoryFrom, MemoryTo)
					gg.getResults(1024)
					gg.editAll(TargetAttributeList, gg.TYPE_DWORD)
				else
					gg.editAll(TargetAttributeList, gg.TYPE_DOUBLE)
				end
				gg.clearResults()
			end
			MemoryFrom = SearchResult[j].address - 0x300
			MemoryTo = SearchResult[j].address
			gg.searchNumber("A0000000h~B0000000h", gg.TYPE_DOUBLE, false, gg.SIGN_EQUAL, MemoryFrom, MemoryTo)
			local AddressResult = gg.getResults(1024)
			if next(AddressResult) == nil then
				gg.searchNumber("A0000000h~B0000000h", gg.TYPE_DWORD, false, gg.SIGN_EQUAL, MemoryFrom, MemoryTo)
				AddressResult = gg.getResults(1024)
			end
			for l = 1, #AddressResult do
				MemoryFrom = AddressResult[l].value
				MemoryTo = AddressResult[l].value + 0x100
				for m = 1, #ShipAttributeList do
					local SplitedAttribute = string.split(tostring(ShipAttributeList[m]), ">")
					local AttributeToSearchList = SplitedAttribute[1]
					local TargetAttributeList = SplitedAttribute[2]
					gg.clearResults()
					gg.searchNumber(AttributeToSearchList, gg.TYPE_DOUBLE, false, gg.SIGN_EQUAL, MemoryFrom, MemoryTo)
					local AttributeResult = gg.getResults(1024)
					if next(AttributeResult) == nil then
						gg.clearResults()
						gg.searchNumber(AttributeToSearchList, gg.TYPE_DWORD, false, gg.SIGN_EQUAL, MemoryFrom, MemoryTo)
						gg.getResults(1024)
						gg.editAll(TargetAttributeList, gg.TYPE_DWORD)
					else
						gg.editAll(TargetAttributeList, gg.TYPE_DOUBLE)
					end
					gg.clearResults()
				end
			end
		end
    end
	gg.setRanges(OriginalRange)
	Exit("修改成功！")
end

function Exit(Message)
    gg.alert(Message)
	os.exit()
end

function Main()
	Choice = gg.choice({
        "改属性",
		"退出",
	}, nil, nil)
	if Choice == 1 then
		ChangeShipAttribute()
	end
	if Choice == 2 then
		Exit("退出成功！")
	end
	FX=false
end

gg.clearResults()
Main()