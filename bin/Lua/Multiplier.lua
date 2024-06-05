function Main1()
	SN = gg.choice({
		"修改面板",
		"还原面板",
		"退出",
	}, nil, "倍率面板")
	if SN==1 then
		HS9()
	end
	if SN==2 then
		HS666()
	end
	if SN==3 then
		exit()
	end
	FX=false
end

function HS9()
    x = gg.prompt({"伤害倍数(默认200倍)"},{"200"},{number})
    n = x[1]
	-- 清除
	gg.clearResults()
	gg.setRanges(32)
	-- 第一次搜索
	gg.searchNumber("0.0001;1::30", gg.TYPE_DOUBLE, false, gg.SIGN_EQUAL, 0, -1, 0)
	gg.refineNumber("1", gg.TYPE_DOUBLE, false, gg.SIGN_EQUAL, 0, -1, 0)
	gg.getResults(100)
	gg.editAll(n, gg.TYPE_DOUBLE)
	gg.getResultCount(results)
	-- 判断
	if results==nil then
		-- 清除
		gg.clearResults()
		gg.setRanges(32)
		-- 第二次搜索
		gg.searchNumber("0.0001E;1D::30", gg.TYPE_DWORD, false, gg.SIGN_EQUAL, 0, -1)
		gg.refineNumber("1D", gg.TYPE_DWORD, false, gg.SIGN_EQUAL, 0, -1)
		gg.getResults(100)
		gg.editAll(n, gg.TYPE_DWORD)
	end
	-- 清除
	gg.clearResults()
	gg.toast("修改成功")
end

function HS666()
    x = gg.prompt({"还原倍数(默认200倍)"},{"200"},{number})
    n = x[1]
	-- 清除
	gg.clearResults()
	gg.setRanges(32)
	-- 第一次搜索
	gg.searchNumber("0.0001;"..n.."::30", gg.TYPE_DOUBLE, false, gg.SIGN_EQUAL, 0, -1, 0)
	gg.refineNumber(n, gg.TYPE_DOUBLE, false, gg.SIGN_EQUAL, 0, -1, 0)
	gg.getResults(100)
	gg.editAll("1", gg.TYPE_DOUBLE)
	gg.getResultCount(results)
	-- 判断
	if results==nil then
		-- 清除
		gg.clearResults()
		gg.setRanges(32)
		-- 第二次搜索
		gg.searchNumber("0.0001E;"..n.."::30", gg.TYPE_DWORD, false, gg.SIGN_EQUAL, 0, -1)
		gg.refineNumber(n, gg.TYPE_DWORD, false, gg.SIGN_EQUAL, 0, -1)
		gg.getResults(100)
		gg.editAll("1", gg.TYPE_DWORD)
	end
	-- 清除
	gg.clearResults()
	gg.toast("还原成功")
end

function exit()
    gg.alert("退出成功")
	os.exit()
end

-- 循环
-- while true do
--	if gg.isVisible(true) then
--		FX=true
--		gg.setVisible(false)
--	end
	gg.clearResults()
--	if FX==true then
		Main1()
--	end
-- end
