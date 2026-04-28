string ch_names[]   = point(0, "pca_channel_names",     @primnum);
float  weights[]    = point(0, "pca_variation_weights", @primnum);
string tag_layers[] = point(0, "pca_tag_layers",        @primnum);

int n = len(ch_names);

for (int i = 0; i < n; i++)
{
    int ch_idx = agentrigfindchannel(0, @primnum, ch_names[i]);
    if (ch_idx >= 0)
        setagentchannelvalue(0, @primnum, weights[i], ch_idx);
}

setagentcurrentlayers(0, @primnum, tag_layers);
