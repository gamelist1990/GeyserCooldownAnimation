// Local GPU evidence reader. Uses RenderDoc's public replay API, no game injection.
#include "renderdoc_replay.h"
REPLAY_PROGRAM_MARKER()
#include <cstdio>
#include <cstring>
#include <cmath>
#include <fstream>
static void visit(IReplayController *controller, const rdcarray<ActionDescription> &actions, const char *directory)
{
  for(const auto &action: actions)
  {
    if(action.numIndices == 72)
    {
      controller->SetFrameEvent(action.eventId, true);
      auto state=controller->GetVulkanPipelineState();
      auto mesh=controller->GetPostVSData(0,0,MeshDataStage::VSOut);
      uint64_t pipeline=0;static_assert(sizeof(pipeline)==sizeof(ResourceId));
      memcpy(&pipeline,&state->graphics.pipelineResourceId,sizeof(pipeline));
      printf("event=%u pipeline=%llu stride=%u vertices_bytes=%llu indices=%u\n", action.eventId,
        (unsigned long long)pipeline, mesh.vertexByteStride,
        (unsigned long long)mesh.vertexByteSize, mesh.numIndices);
      if(mesh.vertexResourceId != ResourceId::Null() && mesh.vertexByteStride>=16)
      {
        uint64_t length=uint64_t(mesh.vertexByteStride)*mesh.numIndices;
        if(mesh.vertexByteSize && mesh.vertexByteSize<length)length=mesh.vertexByteSize;
        auto data=controller->GetBufferData(mesh.vertexResourceId,mesh.vertexByteOffset,length);
        char path[1024];snprintf(path,sizeof(path),"%s/event-%u-vs.csv",directory,action.eventId);
        std::ofstream output(path);output<<"vertex,x,y,z,w,ndc_x,ndc_y\n";
        for(size_t off=0,i=0;off+16<=data.size();off+=mesh.vertexByteStride,i++)
        {
          float position[4];memcpy(position,data.data()+off,16);
          output<<i<<','<<position[0]<<','<<position[1]<<','<<position[2]<<','<<position[3]<<','
            <<position[0]/position[3]<<','<<position[1]/position[3]<<'\n';
        }
      }
      fflush(stdout);
    }
    visit(controller,action.children,directory);
  }
}
int main(int argc,char **argv)
{
  if(argc!=3)return 2;
  setvbuf(stdout,nullptr,_IONBF,0);
  puts("Replay init");
  RENDERDOC_InitialiseReplay(GlobalEnvironment(),{});
  puts("Open capture file");
  ICaptureFile *capture=RENDERDOC_OpenCaptureFile();
  auto status=capture->OpenFile(argv[1],"rdc",nullptr);
  if(!status.OK()){fprintf(stderr,"OpenFile: %s\n",status.internal_msg ? status.internal_msg->c_str() : "API failure");return 3;}
  puts("Create replay controller");
  auto opened=capture->OpenCapture(ReplayOptions(),nullptr);
  puts("Replay controller created");
  if(!opened.first.OK()){fprintf(stderr,"OpenCapture: %s\n",opened.first.internal_msg ? opened.first.internal_msg->c_str() : "API failure");return 4;}
  capture->Shutdown();
  visit(opened.second,opened.second->GetRootActions(),argv[2]);
  opened.second->Shutdown();
  RENDERDOC_ShutdownReplay();
}
