#!/usr/bin/env python3
"""Compile actual Swift bridge methods with recording dependency declarations.
Host boundary regression; no mobile app/backend execution.
"""
from pathlib import Path
import subprocess,tempfile,json,sys
root=Path(__file__).resolve().parents[1]
def method(s,needle):
 start=s.index(needle);op=s.index('{',start);depth=1;i=op+1
 while depth:
  depth+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[start:i]
source=(root/'src/ios/PurchasesPlugin+VirtualCurrencies.swift').read_text()
body=method(source,'func getCachedVirtualCurrencies(')
code="""import Foundation
class CDVInvokedUrlCommand {let callbackId="test"}
enum Status {case ok}
class CDVPluginResult {let message:Any;init(status:Status,messageAs:[String:Any]?=nil){message=messageAs as Any? ?? NSNull()}}
class Delegate {var message:Any=NSNull();func send(_ r:CDVPluginResult,callbackId:String){message=r.message}}
class CommonFunctionality {static var cached:[String:Any]?;static func getCachedVirtualCurrencies()->[String:Any]?{cached}}
class Plugin {let commandDelegate=Delegate()
"""+body+"""
}
let p=Plugin();p.getCachedVirtualCurrencies(command:CDVInvokedUrlCommand())
let absent=p.commandDelegate.message
CommonFunctionality.cached=["all":[:]];p.getCachedVirtualCurrencies(command:CDVInvokedUrlCommand())
let cached=p.commandDelegate.message
CommonFunctionality.cached=nil;p.getCachedVirtualCurrencies(command:CDVInvokedUrlCommand())
let rows:[String:Bool] = ["absentCacheIsNull":absent is NSNull,"populatedCachePreserved":(cached as? [String:Any])?["all"] != nil,"invalidatedCacheIsNull":p.commandDelegate.message is NSNull]
print(String(data:try JSONSerialization.data(withJSONObject:rows,options:[.sortedKeys]),encoding:.utf8)!)
"""
with tempfile.TemporaryDirectory() as tmp:
 path=Path(tmp);(path/'test.swift').write_text(code)
 subprocess.run(['xcrun','swiftc',str(path/'test.swift'),'-o',str(path/'test')],check=True)
 rows=json.loads(subprocess.check_output([str(path/'test')],text=True))
 print(json.dumps(rows,indent=2));print(f"{sum(rows.values())} passed / {sum(not v for v in rows.values())} failed")
 sys.exit(0 if all(rows.values()) else 1)
