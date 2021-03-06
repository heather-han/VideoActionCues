from .base import BaseRecognizer
from .. import builder
from ..registry import RECOGNIZERS
from mmcv.parallel import MMDataParallel
import torch.nn as nn

import torch
import pdb

class TSN3D_bb(nn.Module):

    def __init__(self,
                 backbone,
                 flownet=None,
                 spatial_temporal_module=None,
                 segmental_consensus=None,
                 cls_head=None,
                 train_cfg=None,
                 test_cfg=None,
                 gpus=None):

        super(TSN3D_bb, self).__init__()
        self.backbone = builder.build_backbone(backbone)

        if flownet is not None:
            self.flownet = builder.build_flownet(flownet)

        if spatial_temporal_module is not None:
            self.spatial_temporal_module = builder.build_spatial_temporal_module(
                spatial_temporal_module)
        else:
            raise NotImplementedError

        if segmental_consensus is not None:
            self.segmental_consensus = builder.build_segmental_consensus(
                segmental_consensus)
        else:
            raise NotImplementedError

        if cls_head is not None:
            self.cls_head = builder.build_head(cls_head)
        else:
            raise NotImplementedError

        self.init_weights()
        self.train_cfg = train_cfg
        self.test_cfg = test_cfg

    @property
    def with_flownet(self):
        return hasattr(self, 'flownet') and self.flownet is not None

    @property
    def with_spatial_temporal_module(self):
        return hasattr(self, 'spatial_temporal_module') and self.spatial_temporal_module is not None

    @property
    def with_segmental_consensus(self):
        return hasattr(self, 'segmental_consensus') and self.segmental_consensus is not None

    @property
    def with_cls_head(self):
        return hasattr(self, 'cls_head') and self.cls_head is not None

    def init_weights(self):
        self.backbone.init_weights()

        if self.with_flownet:
            self.flownet.init_weights()

        if self.with_spatial_temporal_module:
            self.spatial_temporal_module.init_weights()

        if self.with_segmental_consensus:
            self.segmental_consensus.init_weights()

        if self.with_cls_head:
            self.cls_head.init_weights()

    def extract_feat_with_flow(self, img_group,
                               trajectory_forward=None,
                               trajectory_backward=None):
        x = self.backbone(img_group,
                          trajectory_forward=trajectory_forward,
                          trajectory_backward=trajectory_backward)
        return x

    def extract_feat(self, img_group):
        x = self.backbone(img_group)
        return x

    def forward(self, img_group_0, gt_label=None, test=False):
        if test == False:
            return self.forward_train(img_group_0, gt_label)
        else:
            return self.forward_test(img_group_0)

    def forward_train(self,
                      img_group_0,
                      gt_label=None,
                      ):
        img_group = img_group_0

        bs = img_group.shape[0]
        img_group = img_group.reshape((-1, ) + img_group.shape[2:])
        num_seg = img_group.shape[0] // bs

        if self.with_flownet:
            raise NotImplementedError
        else:
            feat = self.extract_feat(img_group)
        if self.with_spatial_temporal_module:
            feat = self.spatial_temporal_module(feat)
        if self.with_segmental_consensus:
            feat = feat.reshape((-1, num_seg) + feat.shape[1:])
            feat = self.segmental_consensus(feat)
            feat = feat.squeeze(1)
        losses = dict()
        if self.with_flownet:
            raise NotImplementedError

        if self.with_cls_head:
            cls_score = self.cls_head(feat)
            if gt_label is not None:
                gt_label = gt_label.squeeze()
                loss_cls = self.cls_head.loss(cls_score, gt_label)

                losses['loss_cls'] = loss_cls['loss_cls']
                return feat, losses

        return feat
        #return feat, losses

    def forward_test(self,
                     img_group_0,
                     ):
        #assert num_modalities == 1
        img_group = img_group_0

        bs = img_group.shape[0]
        img_group = img_group.reshape((-1, ) + img_group.shape[2:])
        num_seg = img_group.shape[0] // bs

        if self.with_flownet:
            raise NotImplementedError
        else:
            x = self.extract_feat(img_group)
        if self.with_spatial_temporal_module:
            x = self.spatial_temporal_module(x)
        if self.with_segmental_consensus:
            x = x.reshape((-1, num_seg) + x.shape[1:])
            x = self.segmental_consensus(x)
            x = x.squeeze(1)
        if self.with_cls_head:
            x = self.cls_head(x)

        return x.cpu().numpy()
