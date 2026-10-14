from layout import reorder
x=[{'type':'text','text':'query'},{'type':'text','text':'evidence1'},{'type':'image','image':'pixel1'},{'type':'text','text':'evidence2'},{'type':'image','image':'pixel2'}]
y=reorder(x);assert y==x[1:]+x[:1];assert x[0]['text']=='query';assert [i for i in y if i['type']=='image']==[i for i in x if i['type']=='image'];print('prompt and pixel order preserved; query last passed')
