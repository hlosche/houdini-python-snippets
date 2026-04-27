string ch_names[]   = detail(0, "pca_channel_names", 0);                                                                         
float  weights[]    = detail(0, "pca_variation_weights", 0);                                                                     
int    n            = detail(0, "pca_num_channels", 0);                                                                          
string tag_layers[] = detail(0, "pca_tag_layers", 0);                                                                            

for (int i = 0; i < n; i++)
{
  int ch_idx = agentrigfindchannel(0, @primnum, ch_names[i]);
  if (ch_idx >= 0)
      setagentchannelvalue(0, @primnum, weights[i], ch_idx);
}

setagentcurrentlayers(0, @primnum, tag_layers);
