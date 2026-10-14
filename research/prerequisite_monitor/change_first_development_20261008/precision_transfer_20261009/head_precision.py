def enable_fp32_head(model):
 if model.config.tie_word_embeddings:raise ValueError('tied embeddings would change the body dtype')
 head=model.lm_head;head.float()
 return head.register_forward_pre_hook(lambda module,args:(args[0].float(),)+args[1:])
