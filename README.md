

curl -i -X POST       --url http://localhost:3000/api/base/bse6U9m5sgpVUCjA45t/table       --header 'Authorization: Bearer teable_accdNvfnVYLi5spZPWP_Ev+j1y2wxuQZg2pBxftyeX+H0bVep+FZgpPReWAM/4o='       --header 'Content-Type: application/json'       --data '{"name": "TestLinkTable", "fields": [{"name": "TestLinkField", "type": "link", "options":   {"foreignTableId": "tblnQKUomC8h4FqfAfT", "relationship": "many-to-one"}}]}'
curl -i -X POST       --url http://localhost:3000/api/base/bse6U9m5sgpVUCjA45t/table       --header 'Authorization: Bearer teable_accdNvfnVYLi5spZPWP_Ev+j1y2wxuQZg2pBxftyeX+H0bVep+FZgpPReWAM/4o='       --header 'Content-Type: application/json'       --data '{"name": "TestLinkTable", "fields": [{"name": "TestLinkField", "type": "link", "options":   {"foreignTableId": "bse6U9m5sgpVUCjA45t", "relationship": "many-to-one"}}]}'


curl --request POST \
  --url http://localhost:3000/api/base/bse6U9m5sgpVUCjA45t/table \
  --header 'Authorization: Bearer teable_accdNvfnVYLi5spZPWP_Ev+j1y2wxuQZg2pBxftyeX+H0bVep+FZgpPReWAM/4o='   \
  --header 'content-type: application/json' \
  --data '{"type":"singleSelect","name":"Tags","unique":true,"notNull":true,"dbFieldName":"string","isLookup":true,"description":"this is a summary","lookupOptions":{"foreignTableId":"string","lookupFieldId":"string","linkFieldId":"string","filter":{}},"options":{"expression":"countall({values})","timeZone":"string","formatting":{"date":"string","time":"HH:mm","timeZone":"string"},"showAs":{"type":"url"}},"aiConfig":{"modelKey":"string","isAutoFill":true,"attachPrompt":"string","type":"extraction","sourceFieldId":"string"},"id":"fldxxxxxxxxxxxxxxxx","order":{"viewId":"string","orderIndex":0}}'