package com.agent.misevolution.repository;

import com.agent.misevolution.domain.agent.ServiceExperience;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 服务经验数据访问层
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Mapper
public interface ServiceExperienceMapper {

    /**
     * 插入经验
     */
    int insert(ServiceExperience experience);

    /**
     * 根据ID查询经验
     */
    ServiceExperience selectById(@Param("id") Long id);

    /**
     * 根据实验ID和轮次查询经验
     */
    ServiceExperience findByExperimentAndEpisode(@Param("experimentId") Long experimentId,
                                                  @Param("episode") Integer episode);

    /**
     * 查询实验的违规经验
     */
    List<ServiceExperience> findViolationsByExperiment(@Param("experimentId") Long experimentId,
                                                        @Param("limit") Integer limit);
}
