string selected  = chs("../selected_variation");

string names[]    = detail(0, "pca_variation_names", 0);
float weights[]   = detail(0, "pca_variation_weights", 0);
string ch_names[] = detail(0, "pca_channel_names", 0);
int n             = detail(0, "pca_num_channels", 0);

int var_idx = -1;
for(int i=0; i<len(names); i++)
{
    if(names[i] == selected)
    {
        var_idx = i;
        break;
    }
}

if(var_idx < 0) return;

int offset = var_idx * n;
for(int i =0; i<n; i++)
{
    int ch_idx = agentrigfindchannel(0, @primnum, ch_names[i]);
    if(ch_idx >= 0)
    {
        setagentchannelvalue(0, @primnum, weights[offset + i], ch_idx);
    }
}

