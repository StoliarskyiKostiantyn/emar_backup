$MyApp = Get-WmiObject -Class Win32_Product | Where-Object{$_.Name -eq "eMARVault"}
$MyApp.Uninstall()
