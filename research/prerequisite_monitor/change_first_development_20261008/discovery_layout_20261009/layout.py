def reorder(content):
 assert content and content[0]['type']=='text'
 return content[1:]+content[:1]
